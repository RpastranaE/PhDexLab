"""One master workbook with isolated assay tabs, visible formulas and an experiment index."""
import re
from pathlib import Path
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.chart import BarChart,ScatterChart,Reference,Series
from openpyxl.chart.error_bar import ErrorBars
from openpyxl.chart.data_source import NumDataSource,NumRef
from openpyxl.workbook.properties import CalcProperties
from .excel import text_cell,HEADERS
from .assay_engine import columns,engine,state,cell_plan

ROLES=['RAW','Parameters','Calibration','Processing','Results','Summary','ReadMe','DoseCurve','MassBalance']
HEADERS=dict(HEADERS,DoseCurve=['Sample','Biological unit','Dose (mg/mL final)','Inhibition (%)','Technical SD','Technical n','Local EC50 bracket','Decreasing segment'],MassBalance=['Sample','Biological unit','Loaded (g)','Recovered (g)','Lost (g)','Recovery (%)','QC'])
COLORS={'FRAP':'177E89','ABTS':'4C78A8','CUPRAC':'C17B31','DPPH':'8064A2','TPC':'4A8755','TFC':'B35B75'}

def sheet_name(assay,role):return assay['id']+'_'+role

def validate_ids(assays):
    ids=[a['id'] for a in assays]
    if len(set(ids))!=len(ids) or any(not re.fullmatch(r'A[0-9]{2,3}_[A-Z0-9_]{1,13}',id) for id in ids):raise ValueError('Identificadores de ensayo inválidos o repetidos')
    if len(ids)>40:raise ValueError('Límite del prototipo: 40 ensayos por experimento')

def resolve_formula(formula,names):
    for role in sorted(names,key=len,reverse=True):formula=re.sub(r'(?<![A-Za-z0-9_])'+role+r'!',"'"+names[role]+"'!",formula)
    return formula

def summary_count(rows,p):
    if engine(p)=='sieve':return len({(r['sample_id'],r['lower_um'],r['upper_um']) for r in rows})
    return len({r['sample_id'] for r in rows if r['kind']=='sample'})

def write_master(path,assays,experiment_id,calculated=False):
    validate_ids(assays);wb=Workbook();wb.remove(wb.active)
    index=wb.create_sheet('Index');index.append(['Assay ID','Assay / protocol','Method','State','Information / next step','Source','Result unit'])
    overall=wb.create_sheet('ExperimentSummary');overall.append(['Assay ID','Method','Sample','Biological n','Mean','Biological SD','Unit'])
    registry=wb.create_sheet('Samples');registry.append(['Sample ID','Assays using this ID'])
    meta=wb.create_sheet('_PhDexLab');meta.append(['schema',3,'experiment_id',experiment_id]);meta.append(['Assay ID','Label'])
    sample_ids={}
    report={}
    for assay in assays:
        p=assay['protocol'];status,issue,clean=state(assay);rows=clean if clean is not None else assay.get('rows',[])
        report[assay['id']]=dict(state=status,issue=issue)
        meta.append([assay['id'],assay['label']]);index.append([assay['id'],assay['label'],p['method'],'Pending calculation' if status=='ready' else 'DRAFT',issue or 'Save and close Excel before updating.',p.get('source'),p['result_unit']])
        roles=['RAW','Parameters','Processing','Results','Summary','ReadMe']
        if engine(p) in ('colorimetric','inhibition'):roles.insert(2,'Calibration')
        if engine(p)=='ec50':roles.append('DoseCurve')
        if engine(p)=='sieve':roles.append('MassBalance')
        names={role:sheet_name(assay,role) for role in roles}
        for role,name in names.items():
            ws=wb.create_sheet(name);ws.append(columns(p) if role=='RAW' else HEADERS[role]);ws.sheet_properties.tabColor=COLORS.get(p['method'],'657D89')
        ws=wb[names['RAW']]
        for d in rows:
            for c,key in enumerate(columns(p),1):text_cell(ws.cell(ws.max_row+1 if c==1 else r,c),d.get(key,''));r=ws.max_row
            if d.get('kind')=='sample':sample_ids.setdefault(str(d.get('sample_id','')),set()).add(assay['id'])
        for key,val in p.items():
            ws=wb[names['Parameters']];r=ws.max_row+1;text_cell(ws.cell(r,1),key);text_cell(ws.cell(r,2),val)
        if clean is not None:
            formulas=cell_plan(clean,p)
            for role,cells in formulas.items():
                if role not in names:continue
                for address,formula in cells.items():wb[names[role]][address]=resolve_formula(formula,names)
            result=wb[names['Results']]
            if engine(p) in ('colorimetric','inhibition'):
                for r,((kind,_,_),_) in enumerate(groups_local(clean,{'sample','control'}).items(),2):result.cell(r,9,p['result_unit'] if kind=='sample' else '% recovery')
            else:
                for r in range(2,result.max_row+1):result.cell(r,9,p['result_unit'])
            if 'Calibration' in names:
                cal=wb[names['Calibration']]
                for i,label in enumerate(('Radical control mean' if engine(p)=='inhibition' else 'Reagent blank mean','Slope','Intercept','R-squared','Minimum concentration','Maximum concentration','QC'),2):cal.cell(i,9,label)
                index.cell(index.max_row,4,f'=IF(\'{names["Calibration"]}\'!J3>0,"CALCULATED — review QC","INVALID CALIBRATION")' if calculated else 'Pending calculation')
            elif calculated:index.cell(index.max_row,4,'CALCULATED — review QC')
            summ=wb[names['Summary']]
            for r in range(2,summ.max_row+1):
                overall.append([assay['id'],p['method'],f"='{summ.title}'!A{r}",f"='{summ.title}'!B{r}",f"='{summ.title}'!C{r}",f"='{summ.title}'!D{r}",p['result_unit']])
            add_charts(wb,names,p,clean)
        readme=wb[names['ReadMe']]
        for pair in [('Experiment',experiment_id),('Assay',assay['id']),('Protocol',p['name']),('State',p.get('status')),('Source',p.get('source')),('Notes',p.get('notes')),('Reagents',p.get('reagents')),('Mass basis',p.get('mass_basis')),('Calculation','Excel is the sole production calculation engine; Origin imports saved values.'),('Draft',issue),('Replicates','Average technical readings within each biological unit first. Different sample IDs remain separate.'),('Editing','Edit RAW and Parameters only; save and close Excel, then update. Worksheet names and column keys are managed.'),('Limitations','Draft method transfer; no inferred independence, metrological uncertainty or automatic significance test.')]:readme.append(pair)
        index.cell(index.max_row,2).hyperlink=f"#'{names['RAW']}'!A1";index.cell(index.max_row,2).style='Hyperlink'
    for c,label in enumerate(('RAW','Conditions','Calibration / balance','Results','Summary','Method'),8):index.cell(1,c,label)
    for r,assay in enumerate(assays,2):
        e=engine(assay['protocol']);analysis='Calibration' if e in ('colorimetric','inhibition') else 'DoseCurve' if e=='ec50' else 'MassBalance' if e=='sieve' else None
        for c,role in enumerate(('RAW','Parameters',analysis,'Results','Summary','ReadMe'),8):
            if role:
                cell=index.cell(r,c,role);cell.hyperlink=f"#'{sheet_name(assay,role)}'!A1";cell.style='Hyperlink'
    for sid,ids in sorted(sample_ids.items()):
        if sid:registry.append([sid,', '.join(sorted(ids))])
    for ws in wb:
        if ws==meta:continue
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;ws.sheet_view.showGridLines=False;ws.row_dimensions[1].height=34
        israw=ws.title.endswith('_RAW');isparam=ws.title.endswith('_Parameters')
        for cell in ws[1]:cell.fill=PatternFill('solid',fgColor='173E4A');cell.font=Font(name='Calibri',size=11,bold=True,color='FFFFFF');cell.alignment=Alignment(wrap_text=True,vertical='center')
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                editable=israw or isparam and cell.column==2
                cell.font=Font(name='Calibri',size=11,color='145B9B' if editable else '26373D');cell.fill=PatternFill('solid',fgColor='EAF4FC' if editable else 'F3F7F8' if cell.row%2==0 else 'FFFFFF');cell.alignment=Alignment(wrap_text=True,vertical='top')
                if cell.data_type=='f' or isinstance(cell.value,(int,float)):cell.number_format='0.0000'
            ws.row_dimensions[row[0].row].height=29
        for column in ws.columns:ws.column_dimensions[column[0].column_letter].width=22
        ws.sheet_properties.pageSetUpPr.fitToPage=True;ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
        if isparam or ws.title.endswith('_ReadMe'):ws.column_dimensions['A'].width=32;ws.column_dimensions['B'].width=105
        if israw:ws.column_dimensions['A'].hidden=True
    index.column_dimensions['B'].width=44;index.column_dimensions['E'].width=85;index.column_dimensions['F'].width=55
    from openpyxl.worksheet.datavalidation import DataValidation
    for assay in assays:
        ws=wb[sheet_name(assay,'RAW')];e=engine(assay['protocol'])
        choices='sample' if e in ('gravimetric','sieve') else 'blank,sample' if e=='ec50' else 'blank,standard,control,sample'
        dv=DataValidation(type='list',formula1='"'+choices+'"',allow_blank=True);dv.showErrorMessage=True;dv.error='Seleccionar un tipo válido para este ensayo';ws.add_data_validation(dv);dv.add('B2:B10001')
    meta.sheet_state='veryHidden';wb.calculation=CalcProperties(calcId=0,fullCalcOnLoad=True);wb.save(path);wb.close();return report

def add_charts(wb,names,p,rows):
    if 'Calibration' in names:
        ws=wb[names['Calibration']];last=len(groups_local(rows,{'standard'}))+1
        chart=ScatterChart();chart.title=p['method']+' calibration';chart.x_axis.title=p['equivalent']+' ('+p['concentration_unit']+')';chart.y_axis.title='Inhibition (%)' if engine(p)=='inhibition' else 'Blank-corrected absorbance (AU)'
        series=Series(Reference(ws,min_col=2,min_row=2,max_row=last),Reference(ws,min_col=1,min_row=2,max_row=last),title='Calibration means');series.marker.symbol='circle';series.graphicalProperties.line.noFill=True;chart.series.append(series)
        fit=Series(Reference(ws,min_col=5,min_row=2,max_row=last),Reference(ws,min_col=1,min_row=2,max_row=last),title='OLS fit');chart.series.append(fit);chart.width=22;chart.height=12;ws.add_chart(chart,'A12')
    ws=wb[names['Summary']]
    if ws.max_row>1:
        chart=BarChart();chart.title=p['method']+' | biological mean ± SD';chart.y_axis.title=p['result_unit'];chart.x_axis.title='Sample';chart.add_data(Reference(ws,min_col=3,min_row=1,max_row=ws.max_row),titles_from_data=True);chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=ws.max_row));chart.legend=None;chart.width=22;chart.height=12
        sd=NumDataSource(numRef=NumRef(f"'{ws.title}'!$D$2:$D${ws.max_row}"));chart.series[0].errBars=ErrorBars(errDir='y',errBarType='both',errValType='cust',plus=sd,minus=sd);chart.series[0].graphicalProperties.solidFill='B5D5E5';ws.add_chart(chart,'A'+str(max(7,ws.max_row+3)))

def groups_local(rows,kinds):
    from .calculations import groups
    return groups(rows,kinds)

def read_master(path):
    wb=load_workbook(path,data_only=False,read_only=True)
    try:
        if '_PhDexLab' not in wb:
            from .excel import read_inputs
            rows,p=read_inputs(path);return [dict(id='A01_'+p['method'],label=p['name'],protocol=p,rows=rows)]
        meta=wb['_PhDexLab'];assays=[]
        if meta.cell(1,2).value!=3:raise ValueError('Versión de libro no soportada')
        for meta_row in list(meta.values)[2:]:
            id,label=meta_row[:2]
            if not id:continue
            prefix=str(id);pws=wb[prefix+'_Parameters'];rws=wb[prefix+'_RAW']
            for ws in (pws,rws):
                if any(c.data_type=='f' for row in ws for c in row):raise ValueError('RAW y Parameters deben contener valores, no fórmulas')
            p={r[0]:r[1] for r in pws.iter_rows(min_row=2,values_only=True) if r[0]}
            missing={'method','name','id','version','source','result_unit','concentration_unit','response'}-set(p)
            if missing:raise ValueError('Faltan claves en Parameters: '+', '.join(sorted(missing))+'. Editar valores; no borrar filas de parámetros.')
            from .assay_engine import NUMERIC_PARAMS,yes
            from .data_entry import number
            for key in NUMERIC_PARAMS & set(p):
                try:p[key]=number(p[key])
                except (TypeError,ValueError):pass
            if 'operational_confirmed' in p:p['operational_confirmed']=yes(p['operational_confirmed'])
            keys=columns(p)
            if list(next(rws.values))!=keys:raise ValueError('No cambiar nombres ni orden de columnas RAW')
            rows=[dict(zip(keys,r)) for r in rws.iter_rows(min_row=2,values_only=True) if any(v is not None and str(v).strip() for v in r)]
            import uuid
            for row in rows:
                if not row.get('record_id'):row['record_id']=uuid.uuid4().hex
            assays.append(dict(id=prefix,label=label,protocol=p,rows=rows))
        validate_ids(assays);return assays
    finally:wb.close()

def recalculate_master(path,export_folder):
    import time,pythoncom,win32com.client
    pythoncom.CoInitialize();app=None;book=None;exports=[];export_folder=Path(export_folder);export_folder.mkdir(parents=True,exist_ok=True)
    try:
        app=win32com.client.DispatchEx('Excel.Application');app.Visible=False;app.DisplayAlerts=False;app.AskToUpdateLinks=False;app.AutomationSecurity=3
        app.ScreenUpdating=False;app.EnableEvents=False
        book=app.Workbooks.Open(str(Path(path).resolve()),UpdateLinks=0,ReadOnly=False)
        if book.ReadOnly:raise RuntimeError('Excel abrió el libro en solo lectura; cerrar el archivo y repetir')
        app.CalculateFullRebuild();deadline=time.monotonic()+120
        while app.CalculationState!=0:
            if time.monotonic()>deadline:raise TimeoutError('Excel no terminó de recalcular')
            pythoncom.PumpWaitingMessages();time.sleep(.1)
        for ws in book.Worksheets:
            if ws.Name.endswith(('_Summary','_Calibration')):
                for i in range(1,ws.ChartObjects().Count+1):
                    try:
                        obj=ws.ChartObjects(i);ws.Activate();obj.Activate();chart=obj.Chart
                        chart.Axes(1).TickLabels.NumberFormat='General';chart.Axes(2).TickLabels.NumberFormat='General'
                        if chart.Axes(2).HasTitle:
                            unit=chart.Axes(2).AxisTitle.Text;chart.Axes(2).HasTitle=False;chart.ChartTitle.Text=ws.Name.split('_')[1]+' | '+unit
                        if chart.Axes(1).HasTitle:chart.Axes(1).AxisTitle.Top=obj.Height-40
                        if chart.HasLegend:chart.Legend.Top=obj.Height-23
                    except Exception:
                        pass  # Optional chart geometry differs across desktop Excel builds; values are already calculated.
                if ws.Name.endswith('_Summary') and ws.UsedRange.Rows.Count>1:
                    target=export_folder/(ws.Name+'.pdf');ws.ExportAsFixedFormat(0,str(target.resolve()));exports.append(target)
        book.Save()
        return exports
    finally:
        if book is not None:book.Close(SaveChanges=False)
        if app is not None:app.Quit()
        pythoncom.CoUninitialize()
