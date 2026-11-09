"""One native Origin project with Data/Graphs folders for every assay."""
import json
import re
import time
import copy
from .paths import Layout
from .multi_excel import sheet_name
from .excel import values
from .assay_engine import engine
from .origin import remove_empty_default_book
from .multi_publication import payload,labels,captions,BLUE,ORANGE
from .publication import finite
from .graph_styles import for_experiment,role_style,sample_color
from .protocols import digest
from .integration import file_hash
from .export_cache import store,restore

def prepare_assay_folders(op,managed,aid):
    """One round trip instead of repeated mkdir/cd + temporary-path queries."""
    path=managed.rstrip('/')+'/'+aid+'/';data=path+'Data/';graphs=path+'Graphs/'
    op.lt_exec(f'pe_cd path:="{managed}";pe_mkdir folder:="{aid}" chk:=1;pe_cd path:="{path}";pe_mkdir folder:="Data" chk:=1;pe_mkdir folder:="Graphs" chk:=1;pe_cd path:="{data}";')
    return path,data,graphs

def style_graph_fast(gp,layer,xlabel,ylabel,typography=None):
    """Same print geometry as style_graph, with batched LabTalk properties."""
    typography=typography or dict(font='Arial',tick_size=8,label_size=9)
    gp.set_int('aa',1)
    layer.lt_exec('page.width=page.resx*4.3307;page.height=page.resy*3.1496;layer.unit=1;layer.left=22;layer.top=10;layer.width=72;layer.height=65;'
        'layer.x.showgrids=0;layer.y.showgrids=0;layer.x.opposite=0;layer.y.opposite=0;'
        'layer.x.label.font=font(Arial);layer.y.label.font=font(Arial);layer.x.label.numFormat=1;layer.y.label.numFormat=1;'
        'layer.x.thickness=1;layer.y.thickness=1;layer.x.ticks=1;layer.y.ticks=1;layer.x.label.pt=8;layer.y.label.pt=8;'
        'xb.fsize=9;yl.fsize=9;xb.font=font(Arial);yl.font=font(Arial);xb.showframe=0;yl.showframe=0;')
    font=typography['font'];tick=typography['tick_size'];label=typography['label_size']
    layer.lt_exec(f'layer.x.label.font=font({font});layer.y.label.font=font({font});layer.x.label.pt={tick};layer.y.label.pt={tick};xb.font=font({font});yl.font=font({font});xb.fsize={label};yl.fsize={label};')
    layer.label('xb').text=xlabel;layer.label('yl').text=ylabel

def remove_empty_starter_folders(op):
    """Only untouched root Folder01/Folder1 placeholders; never remove user content."""
    removed=[];root=op.pe.root_folder();op.pe.cd(root.path)
    for child in list(root.obj.GetFolders()):
        path=child.GetPath();name=path.rstrip('/\\').replace('\\','/').split('/')[-1]
        if re.fullmatch(r'Folder0*1',name,re.IGNORECASE) and not list(child.PageBases()) and not list(child.GetFolders()):
            op.lt_exec(f'pe_rmdir folder:="{path}" folpromt:=0 pgpromt:=0;');removed.append(path)
    return removed


def move_if_needed(op,name,path,current=None):
    normal=lambda value:str(value).replace('\\','/').rstrip('/').casefold()
    if normal(op.pe.search(name) if current is None else current)!=normal(path):op.pe.move(name,path)

def sync(folder,assays,states,mode='connector',notify=lambda *args:None,force=False):
    import originpro as op
    l=Layout(folder);style=for_experiment(folder);report={'mode':mode,'auto_sync_verified':False,'relative_paths_verified':False,'errors':[],'exports':[],'assays':{},'presentation':style}
    previous=l.meta/'origin_status.json';old_status=json.loads(previous.read_text(encoding='utf-8')) if previous.exists() else {}
    restyle=old_status.get('presentation')!=style
    project_verified=l.project.exists() and old_status.get('project_sha256')==file_hash(l.project)
    trust=(not force and project_verified and old_status.get('master_path')==str(l.master) and old_status.get('mode')==mode)
    old_paths=old_status.get('page_folders',{}) if project_verified else {}
    page_paths={}
    def existing_path(name):return old_paths.get(name) or op.pe.search(name)
    report.update(table_hashes={},graphs={},reused_tables=[],reused_graphs=[],master_path=str(l.master),operation_seconds={},style_readback={})
    try:
        if l.project.exists():
            if not op.open(str(l.project)):raise RuntimeError('No se pudo abrir el proyecto Origin')
        else:op.new()
        report['origin_version']=str(op.lt_float('@V'));root=op.pe.root_folder().path;op.pe.cd(root)
        managed=op.pe.mkdir('PhDexLab',True)
        # Preserve old v0.4 pages by moving them, never discard user content on migration.
        legacy=[pg for pg in op.pe.root_folder().pages() if pg.name!='Book1']
        if legacy:
            old=op.pe.mkdir('Legacy_v04',True)
            for pg in legacy:op.pe.move(pg.name,old)
        previous=l.meta/'origin_status.json'
        if previous.exists():
            old_status=json.loads(previous.read_text(encoding='utf-8'));removed=set(old_status.get('assays',{}))-{a['id'] for a in assays}
            for aid in sorted(removed):
                op.pe.cd(managed);archive_path=op.pe.mkdir('Archived_assays',True);op.pe.move(aid,archive_path)
        for count,a in enumerate(assays,1):
            aid=a['id'];short=aid.split('_')[0];p=a['protocol'];notify(4,f'Origin: {count}/{len(assays)} · {a["label"]}')
            # A verified unchanged project + identical assay tables is stronger than another import.
            # Reuse only artifacts whose bytes also match their content-addressed cache.
            expected_roles=['RAW','Parameters','Results','Summary']
            if engine(p) in ('colorimetric','inhibition'):expected_roles.append('Calibration')
            if engine(p)=='ec50':expected_roles.append('DoseCurve')
            if engine(p)=='sieve':expected_roles.append('MassBalance')
            hashes={aid+'/'+role:digest(values(l.master,sheet_name(a,role))) for role in expected_roles}
            graph_keys=[short+'ResG']+([short+'CalG'] if 'Calibration' in expected_roles else [])+([short+'DoseG'] if 'DoseCurve' in expected_roles else [])
            old_assay=old_status.get('assays',{}).get(aid,{})
            reusable=(trust and not restyle and states[aid]['state']=='calculated' and old_assay.get('state')=='calculated'
                and all(old_status.get('table_hashes',{}).get(key)==sha for key,sha in hashes.items())
                and all(key in old_status.get('graphs',{}) for key in graph_keys))
            if reusable and all(restore(folder,old_status['graphs'][key].get('files',{})) for key in graph_keys):
                notify(4,f'Origin · {aid}: resultados sin cambios verificados')
                report['assays'][aid]=dict(copy.deepcopy(old_assay),cached_readback=True);report['table_hashes'].update(hashes);report['reused_tables'].extend(hashes)
                for key in graph_keys:
                    report['graphs'][key]=old_status['graphs'][key];report['reused_graphs'].append(key);report['exports'].extend(old_status['graphs'][key]['files'])
                page_paths.update({name:path for name,path in old_paths.items() if name.startswith(short)})
                dest=l.figures/aid/'Origin';dest.mkdir(parents=True,exist_ok=True);(dest/(l.stem+'_'+aid+'_captions.txt')).write_text(captions(payload(folder,a),style['results']['marker']!='none'),encoding='utf-8')
                continue
            assay_path,data_path,graphs_path=prepare_assay_folders(op,managed,aid)
            ar=report['assays'][aid]={'folder':assay_path,'state':states[aid]['state'],'readback':{}};sheets={}
            roles=['RAW','Parameters','Results','Summary']
            if engine(p) in ('colorimetric','inhibition'):roles.append('Calibration')
            if engine(p)=='ec50':roles.append('DoseCurve')
            if engine(p)=='sieve':roles.append('MassBalance')
            codes={'RAW':'Raw','Parameters':'Par','Results':'Res','Summary':'Sum','Calibration':'Cal','DoseCurve':'Dose','MassBalance':'Mass'}
            for role in roles:
                notify(4,f'Origin · {aid}: importando {role}')
                tick=time.perf_counter();name=short+codes[role];book=op.find_book('w',name);existed=book is not None
                location=existing_path(book.name) if existed else data_path
                if existed and not location.casefold().startswith(assay_path.casefold()):raise RuntimeError('Nombre Origin en conflicto fuera del ensayo: '+name)
                if book is None:book=op.new_book('w',lname=a['label']+' · '+role);book.name=name
                ws=book[0];ws.name='Values'
                if existed:move_if_needed(op,book.name,data_path,current=location)
                page_paths[book.name]=data_path
                table=values(l.master,sheet_name(a,role));table_key=aid+'/'+role;table_hash=digest(table);report['table_hashes'][table_key]=table_hash
                reused=trust and old_status.get('table_hashes',{}).get(table_key)==table_hash and existed
                if reused:report['reused_tables'].append(table_key)
                elif mode=='connector':
                    dc=op.Connector(ws,dctype='Excel',keep_DC=True);settings=dc.settings();settings['mainheader']=0;settings['labels'][op.attrib_key('Use')]='1';settings['labels']['longname']=1;dc.imp(str(l.master),sel=sheet_name(a,role))
                else:
                    ws.remove_DC();ws.clear()
                    for c,label in enumerate(table[0]):ws.from_list(c,[r[c] if c<len(r) else None for r in table[1:]],lname=str(label or ''))
                sheets[role]=ws
                if role in ('Summary','Results','Calibration','DoseCurve'):
                    y={'Summary':2,'Results':4,'Calibration':1,'DoseCurve':3}[role];expected=values(l.master,sheet_name(a,role))[1:];actual=ws.to_list(y)
                    for i,row in enumerate(expected):
                        if finite(row[y]) and (i>=len(actual) or abs(float(actual[i])-row[y])>max(1e-10,abs(row[y])*1e-10)):raise RuntimeError(f'Origin/Excel no coinciden: {aid}, {role}, fila {i+2}')
                    ar['readback'][role]=sum(finite(r[y]) for r in expected)
                report['operation_seconds'][table_key]=round(time.perf_counter()-tick,4)
            if states[aid]['state'] not in ('calculated','needs_review'):
                # Current data can be inspected; stale managed graphs are removed only after archival by caller.
                for suffix in ('CalG','ResG','DoseG'):
                    g=op.find_graph(short+suffix)
                    if g:g.destroy()
                continue
            data=payload(folder,a);op.pe.cd(data_path);points_book=op.find_book('w',short+'Pts')
            points_existed=points_book is not None
            if points_book is None:points_book=op.new_book('w',lname=a['label']+' · Biological points');points_book.name=short+'Pts'
            points=points_book[0];points.clear();xs=[];ys=[];point_samples=[]
            for i,row in enumerate(data['summary'],1):
                bio=[r for r in data['results'] if r[0]=='sample' and r[1]==row[0] and finite(r[4])]
                for j,r in enumerate(bio):xs.append(i+(0 if len(bio)==1 else -.13+.26*j/(len(bio)-1)));ys.append(r[4]);point_samples.append(i-1)
            points.from_list(0,xs,lname='Sample position');points.from_list(1,ys,lname='Biological-unit mean')
            if points_existed:move_if_needed(op,points_book.name,data_path,current=existing_path(points_book.name))
            page_paths[points_book.name]=data_path
            xlab,ylab,reslab=labels(p);op.pe.cd(graphs_path)
            specs=[('Summary','ResG',2,0,'column','results')]
            if 'Calibration' in sheets:specs.append(('Calibration','CalG',1,0,'scatter','calibration'))
            if 'DoseCurve' in sheets:specs.append(('DoseCurve','DoseG',3,2,'scatter','dose_response'))
            for role,suffix,y,x,template,stem in specs:
                notify(4,f'Origin · {aid}: gráfica {stem}')
                gp=op.find_graph(short+suffix)
                dose_layout=digest([r[:3] for r in data['curve']]) if role=='DoseCurve' else None
                if gp is not None and role=='DoseCurve' and old_status.get('graphs',{}).get(short+suffix,{}).get('dose_layout')!=dose_layout:gp.destroy();gp=None
                if gp is not None and restyle:gp.destroy();gp=None
                graph_existed=gp is not None
                # Managed graph data layout is stable; keep editable formatting after first creation.
                if gp is None:
                    gp=op.new_graph(template=template);gp.name=short+suffix;gp.lname=p['method']+' '+stem.replace('_',' ');gl=gp[0]
                    visual=role_style(style,{'Summary':'results','Calibration':'calibration','DoseCurve':'dose'}[role])
                    curve_plots=[]
                    if role=='DoseCurve':
                        keys=sorted({tuple(row[:2]) for row in data['curve']})
                        for curve_index,curve_key in enumerate(keys):
                            rows=[i for i,row in enumerate(data['curve']) if tuple(row[:2])==curve_key]
                            if rows!=list(range(rows[0],rows[-1]+1)):raise RuntimeError('Dose curve rows must be contiguous per biological unit')
                            rg=f'{sheets[role].lt_range(False)}!(3,4,5,)[{rows[0]+1}:{rows[-1]+1}]'
                            curve=gl.add_plot(rg,type='y');curve.color=visual['colors'][curve_index%len(visual['colors'])];curve.symbol_kind=visual['symbol'];curve.symbol_interior=1 if visual['open'] else 0;curve.symbol_size=visual['size']
                            gl.lt_exec(f'range _phdex_curve={curve.lt_range()};set _phdex_curve -d {visual["line_origin"]};set _phdex_curve -wp {visual["width"]};')
                            gl.plot_list()[-1].color=visual['error'];curve_plots.append(curve)
                        plot=curve_plots[0]
                    else:
                        plot=gl.add_plot(sheets[role],coly=y,colx=x,colyerr=3,type='c' if role=='Summary' else 's');plot.color=visual['fill'] if role=='Summary' else visual['colors'][0]
                    if role!='Summary':plot.symbol_kind=visual['symbol'];plot.symbol_interior=1 if visual['open'] else 0;plot.symbol_size=visual['size']
                    if role=='Calibration':
                        line=gl.add_plot(sheets[role],coly=4,colx=0,type='l');line.color=visual['colors'][1]
                        gl.lt_exec(f'range _phdex_line={line.lt_range()};set _phdex_line -d {visual["line_origin"]};set _phdex_line -wp {visual["width"]};get _phdex_line -d _phdex_dash;')
                    if role=='Summary':
                        gl.lt_exec(f'range _phdex_fill={plot.lt_range()};set _phdex_fill -pfb {op.ocolor(visual["fill"])};set _phdex_fill -pbc {op.ocolor(visual["colors"][0])};')
                        dot=gl.add_plot(points,coly=1,colx=0,type='s');dot.color=visual['colors'][0];dot.symbol_size=visual['size'];dot.symbol_kind=visual['symbol'];dot.symbol_interior=1 if visual['open'] else 0
                    error_plot=gl.plot_list()[1];error_plot.color=visual['error']
                    symbol_plots=curve_plots if role=='DoseCurve' else [dot if role=='Summary' else plot]
                    for symbol_index,symbol_plot in enumerate(symbol_plots):
                        symbol_color=op.ocolor(visual['colors'][symbol_index%len(visual['colors'])]);fill_color=op.ocolor('#FFFFFF') if visual['open'] else symbol_color
                        gl.lt_exec(f'range _phdex_symbol={symbol_plot.lt_range()};set _phdex_symbol -cse {symbol_color};set _phdex_symbol -csf {fill_color};set _phdex_symbol -kf {1 if visual["open"] else 0};')
                    styled=dot if role=='Summary' else plot
                    readback=dict(symbol=int(styled.symbol_kind),interior=int(styled.symbol_interior),color=styled.color)
                    if readback['symbol']!=visual['symbol'] or readback['interior']!=(1 if visual['open'] else 0):raise RuntimeError('Origin no aplicó el símbolo del estilo seleccionado')
                    if role=='Calibration':
                        readback['line_style']=int(op.lt_int('_phdex_dash'))
                        if readback['line_style']!=visual['line_origin']:raise RuntimeError('Origin no aplicó el tipo de línea del estilo seleccionado')
                    report['style_readback'][short+suffix]=readback
                    legend=gl.label('Legend')
                    if legend:
                        if role=='DoseCurve':
                            legend.set_int('fsize',7);legend.set_int('showframe',0);legend.text='\n'.join('\\l('+str(curve.index()+1)+') '+' / '.join(map(str,key)) for curve,key in zip(curve_plots,keys))
                        else:legend.remove()
                    style_graph_fast(gp,gl,'Sample' if role=='Summary' else xlab,reslab if role=='Summary' else ylab,style['typography'])
                if graph_existed:move_if_needed(op,gp.name,graphs_path,current=existing_path(gp.name))
                page_paths[gp.name]=graphs_path;gl=gp[0];gl.rescale();gl.label('xb').text='Sample' if role=='Summary' else xlab;gl.label('yl').text=reslab if role=='Summary' else ylab
                if role=='DoseCurve':
                    gp.lt_exec('page.width=page.resx*6.8;page.height=page.resy*3.8;layer.unit=1;layer.left=16;layer.width=52;')
                    legend=gl.label('Legend')
                    if legend:
                        legend.set_int('fsize',7);legend.set_int('showframe',0);legend.set_int('font',op.lt_int('font('+style['typography']['font']+')'))
                        legend.set_float('x1',gl.get_float('x.to')+.05*(gl.get_float('x.to')-gl.get_float('x.from')))
                        legend.set_float('y1',gl.get_float('y.to')-.03*(gl.get_float('y.to')-gl.get_float('y.from')))
                if role=='Summary':
                    gl.set_xlim(.4,len(data['summary'])+.6,1)
                    if style['results']['per_sample']:
                        plots=gl.plot_list();bars=plots[0];dots=plots[-1];commands=[f'range _phdex_bars={bars.lt_range()};range _phdex_dots={dots.lt_range()};']
                        for i in range(len(data['summary'])):
                            color=op.ocolor(sample_color(style,i));commands.append(f'set _phdex_bars {i+1} -pfb {color};set _phdex_bars {i+1} -pbc {color};')
                        for i,sample in enumerate(point_samples):
                            color=op.ocolor(sample_color(style,sample));commands.append(f'set _phdex_dots {i+1} -c {color};set _phdex_dots {i+1} -cse {color};'+('' if style['results']['open'] else f'set _phdex_dots {i+1} -csf {color};'))
                        gl.lt_exec(''.join(commands))
                key=short+suffix;signature=digest(dict(table=report['table_hashes'][aid+'/'+role],results=data['results'] if role=='Summary' else None,protocol=p,style=style))
                old_graph=old_status.get('graphs',{}).get(key,{})
                if trust and not restyle and old_graph.get('signature')==signature and restore(folder,old_graph.get('files',{})):
                    report['graphs'][key]=old_graph;report['exports'].extend(old_graph['files']);report['reused_graphs'].append(key);continue
                graph_files=[]
                for ext in ('png','pdf','svg'):
                    dest=l.figures/aid/'Origin'/ext.upper();dest.mkdir(parents=True,exist_ok=True);path=dest/(l.stem+'_'+aid+'_'+stem+'.'+ext)
                    try:
                        tick=time.perf_counter()
                        gp.save_fig(str(path),width=2600 if ext=='png' else 0)
                        report['operation_seconds'][key+'/'+ext]=round(time.perf_counter()-tick,4)
                        if not path.exists() or path.stat().st_size==0:raise RuntimeError('No se creó el archivo')
                        report['exports'].append(str(path.relative_to(l.root)))
                        graph_files.append(str(path.relative_to(l.root)))
                    except Exception as error:report['errors'].append(f'{aid}/{ext}: {error}')
                if len(graph_files)==3:report['graphs'][key]=dict(signature=signature,dose_layout=dose_layout,files=store(folder,graph_files))
            dest=l.figures/aid/'Origin';(dest/(l.stem+'_'+aid+'_captions.txt')).write_text(captions(data,style['results']['marker']!='none'),encoding='utf-8')
        report['removed_empty_default_books']=remove_empty_default_book(op);report['removed_empty_starter_folders']=remove_empty_starter_folders(op);op.pe.cd(managed);op.save(str(l.project));report['project_saved']=l.project.exists()
        report['root_folders']=[child.GetPath() for child in op.pe.root_folder().obj.GetFolders()]
        saved_root=op.pe.root_folder().path
        def saved_path(path):return saved_root+path[len(root):] if path.startswith(root) else path
        report['page_folders']={name:saved_path(path) for name,path in page_paths.items()}
        for ar in report['assays'].values():ar['folder']=saved_path(ar['folder'])
        if not report['project_saved']:raise RuntimeError('Origin no guardó el proyecto')
    finally:
        try:op.exit()
        except Exception:pass
    report['project_sha256']=file_hash(l.project)
    (l.meta/'origin_status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8');return report
