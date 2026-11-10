"""Native editable Origin 2024 figures; calculations remain owned by Excel."""
import json
from .paths import Layout
from .ui_fields import axis_labels

STYLE_VERSION=5

def style_graph(gp,layer,xlabel,ylabel):
    import originpro as op
    gp.set_int('aa',1)
    # Unlike the display unit, page.width/height are always printer dots.
    gp.lt_exec('page.width=page.resx*4.3307;page.height=page.resy*3.1496;')
    layer.lt_exec('layer.unit=1;layer.left=22;layer.top=10;layer.width=72;layer.height=65;')
    layer.set_int('x.showgrids',0);layer.set_int('y.showgrids',0)
    layer.set_int('x.opposite',0);layer.set_int('y.opposite',0)
    layer.lt_exec('layer.x.label.font=font(Arial);layer.y.label.font=font(Arial);layer.x.label.numFormat=1;layer.y.label.numFormat=1;layer.x.thickness=1;layer.y.thickness=1;layer.x.ticks=1;layer.y.ticks=1;layer.x.label.pt=8;layer.y.label.pt=8;')
    layer.label('xb').text=xlabel;layer.label('yl').text=ylabel
    for key in ('xb','yl'):
        label=layer.label(key)
        if label:
            label.set_int('fsize',9);label.set_int('font',int(op.lt_int('font(Arial)')));label.set_int('showframe',0)

def native_labels(p):
    unit='µmol L\\+(-1)' if p['concentration_unit']=='umol/L' else 'mg L\\+(-1)'
    basis='before reaction' if p['calibration_basis']=='before' else 'final reaction mixture'
    x=f"{p['equivalent']} concentration ({unit})\n{basis}"
    wavelength=f"{p['wavelength_nm']:g}"
    y='Blank-corrected '+('\\g(D)' if p['response']=='delta' else '')+f'A\\-({wavelength}) (AU)'
    result='FRAP (µmol Fe(II) eq g\\+(-1))' if p['equivalent']=='Fe(II)' else 'FRAP (mg TE 100 g\\+(-1))'
    return x,y,result

def english_ticks(layer,axis):
    start=layer.get_float(axis+'.from');end=layer.get_float(axis+'.to');step=layer.get_float(axis+'.inc')
    if step<=0:return
    import math
    first=math.ceil((start-1e-10)/step)*step
    count=int(round((end-first)/step))+1
    if not 1<=count<=30:return
    labels=' '.join(f'{first+i*step:.4g}' for i in range(count))
    layer.set_int(axis+'.label.type',10);layer.set_str(axis+'.label.string',labels)

def remove_empty_default_book(op):
    """Remove only Origin's untouched starter Book1; preserve books with data or labels."""
    removed=[]
    for book in list(op.pages('w')):
        if book.name!='Book1':continue
        sheets=list(book)
        if not sheets or any(ws.name!='Sheet1' or ws.rows>0 for ws in sheets):continue
        # Custom labels can contain user content even with no data rows.
        if any(any(str(v or '').strip() for v in ws.get_labels('L')+ws.get_labels('U')+ws.get_labels('C')) for ws in sheets):continue
        book.destroy();removed.append('Book1')
    return removed

def sync(folder, mode='connector'):
    import originpro as op
    from .excel import values
    from .publication import payload,captions,finite,BLUE,ORANGE
    layout=Layout(folder);layout.prepare();project=layout.project;data=payload(folder)
    report={'mode':mode,'auto_sync_verified':False,'relative_paths_verified':False,'exports':[],'errors':[],'style_version':STYLE_VERSION}
    previous={};status=layout.meta/'origin_status.json'
    if status.exists():
        try:previous=json.loads(status.read_text(encoding='utf-8'))
        except ValueError:pass
    try:
        if project.exists():
            if not op.open(str(project)):raise RuntimeError('No se puede abrir el proyecto Origin')
        else:op.new()
        report['origin_version']=str(op.lt_float('@V'));sheets={}
        for sheet,name,ycol in (('Calibration','CalibrationData',1),('Summary','SummaryData',2),('Results','ResultsData',4)):
            ws=op.find_sheet('w',name);new=ws is None
            if new:ws=op.new_sheet('w',lname=name);ws.name=name
            if mode=='connector':
                dc=op.Connector(ws,dctype='Excel',keep_DC=True);settings=dc.settings()
                settings['mainheader']=0;settings['labels'][op.attrib_key('Use')]='1';settings['labels']['longname']=1
                dc.imp(str(layout.master),sel=sheet)
                if ws.rows<1:raise RuntimeError(f'Excel Connector no importó {sheet}')
            else:
                table=values(layout.master,sheet)
                if not new:ws.remove_DC()
                ws.clear()
                for c,label in enumerate(table[0]):ws.from_list(c,[r[c] for r in table[1:]],lname=str(label or ''))
            expected=values(layout.master,sheet);observed=ws.to_list(ycol)
            for i,row in enumerate(expected[1:]):
                if finite(row[ycol]) and (i>=len(observed) or abs(float(observed[i])-row[ycol])>max(1e-10,abs(row[ycol])*1e-10)):
                    raise RuntimeError(f'Origin y Excel no coinciden: {sheet}, fila {i+2}')
            report.setdefault('readback',{})[sheet]={'matched_numeric_rows':sum(finite(r[ycol]) for r in expected[1:])}
            sheets[sheet]=ws
        points=op.find_sheet('w','BiologicalPoints')
        if points is None:points=op.new_sheet('w',lname='BiologicalPoints');points.name='BiologicalPoints'
        points.clear();xs=[];ys=[]
        for i,row in enumerate(data['summary'],1):
            bio=[r for r in data['results'] if r[1]==row[0]]
            for j,r in enumerate(bio):
                xs.append(i+(0 if len(bio)==1 else -0.13+0.26*j/(len(bio)-1)));ys.append(r[4])
        points.from_list(0,xs,lname='Sample position');points.from_list(1,ys,lname='Experimental-unit mean')
        xlabel,ylabel,resultlabel=native_labels(data['protocol'])
        for sheet,name,ycol,xcol,template in (('Calibration','CalGraph',1,0,'scatter'),('Summary','ResultGraph',2,0,'column')):
            gp=op.find_graph(name);rebuild=gp is None or previous.get('style_version')!=STYLE_VERSION
            if rebuild and gp is not None:gp.destroy();gp=None
            if gp is None:
                gp=op.new_graph(template=template);gp.name=name;gp.lname='FRAP calibration' if sheet=='Calibration' else 'FRAP results';gl=gp[0]
                plot=gl.add_plot(sheets[sheet],coly=ycol,colx=xcol,colyerr=3,type='s' if sheet=='Calibration' else 'c');plot.color=BLUE
                if sheet=='Calibration':
                    plot.symbol_size=4
                    line=gl.add_plot(sheets[sheet],coly=4,colx=0,type='l');line.color=ORANGE;line.set_cmd('-w 250')
                else:
                    plot.color='#B5D5E5'
                    dot=gl.add_plot(points,coly=1,colx=0,type='s');dot.color=BLUE;dot.symbol_size=4
                legend=gl.label('Legend')
                if legend:legend.remove()
                style_graph(gp,gl,xlabel if sheet=='Calibration' else 'Sample',ylabel if sheet=='Calibration' else resultlabel)
            gl=gp[0];gl.rescale()
            gl.label('xb').text=xlabel if sheet=='Calibration' else 'Sample'
            gl.label('yl').text=ylabel if sheet=='Calibration' else resultlabel
            if sheet=='Summary':gl.set_xlim(0.4,len(data['summary'])+0.6,1)
            if sheet=='Calibration':
                text=f"y = {data['slope']:.4g}x {data['intercept']:+.4g}\nR\\+(2) = {data['r2']:.4f}"
                gl.lt_exec('label -p 10 10 -n FitStats Fit;');label=gl.label('FitStats')
                if label:
                    label.text=text;label.set_int('fsize',8);label.set_int('font',int(op.lt_int('font(Arial)')));label.set_int('showframe',0)
                    label.set_float('x1',gl.get_float('x.from')+0.05*(gl.get_float('x.to')-gl.get_float('x.from')))
                    label.set_float('y1',gl.get_float('y.to')-0.05*(gl.get_float('y.to')-gl.get_float('y.from')))
            english_ticks(gl,'y')
            if sheet=='Calibration':english_ticks(gl,'x')
            for ext in ('png','pdf','svg'):
                path=layout.origin_figures(ext)/(layout.stem+('_calibration' if sheet=='Calibration' else '_frap_results')+'.'+ext)
                try:
                    gp.save_fig(str(path),width=2600 if ext=='png' else 0)
                    if not path.exists() or path.stat().st_size==0:raise RuntimeError('Archivo no creado')
                    report['exports'].append(str(path.relative_to(layout.root)))
                except Exception as e:report['errors'].append(f'{ext}: {e}')
        report['removed_empty_default_books']=remove_empty_default_book(op)
        report['workbooks']=[book.name for book in op.pages('w')]
        op.save(str(project))
        if not project.exists():raise RuntimeError('No se ha guardado el proyecto Origin')
        report['project_saved']=True
    finally:
        try:op.exit()
        except Exception:pass
    (layout.figures/'Origin'/(layout.stem+'_captions.txt')).write_text(captions(data),encoding='utf-8')
    status.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return report
