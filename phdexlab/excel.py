"""Generate a new managed workbook, then calculate with Microsoft Excel.

openpyxl is the portable application dependency, not a calculation engine.
"""
import time
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.chart import ScatterChart, BarChart, Series, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from .data_entry import COLUMNS, normalize
from .calculations import plan
from .protocols import validate
from .ui_fields import axis_labels

HEADERS = {
    "Summary": ["Sample", "Biological n", "Mean", "Biological SD"],
    "RAW": COLUMNS,
    "Parameters": ["Parámetro", "Valor"],
    "Processing": ["record_id", "Respuesta bruta", "Respuesta corregida", "C equivalente eje", "Resultado / Recuperación %"],
    "Calibration": ["Standard concentration", "Mean response", "Technical n", "Response SD", "OLS prediction", "Residual", "", "", "Metric", "Value"],
    "Results": ["kind", "Sample", "Biological unit", "Technical n", "Mean", "Technical SD", "CV (%)", "QC", "Unit"],
    "ReadMe": ["Concepto", "Detalle"],
}

def text_cell(cell, value):
    cell.value = value
    if isinstance(value, str):
        cell.data_type = "s"  # IDs/notes beginning '=' remain text, never injected formulas.

def write_book(path, rows, protocol, experiment_id):
    p = validate(protocol); rows = normalize(rows,p)
    wb = Workbook(); wb.remove(wb.active)
    for name, headers in HEADERS.items():
        ws = wb.create_sheet(name); ws.append(headers)
    for d in rows:
        ws=wb["RAW"]; r=ws.max_row+1
        for c,key in enumerate(COLUMNS,1):
            text_cell(ws.cell(r,c), d[key])
    for key,value in p.items():
        ws=wb["Parameters"]; r=ws.max_row+1
        text_cell(ws.cell(r,1),key); text_cell(ws.cell(r,2),value)
    for sheet,cells in plan(rows,p).items():
        for address,formula in cells.items():
            wb[sheet][address] = formula
    for i,label in enumerate(("Blanco medio", "Pendiente", "Intercepto", "R²", "C mínima", "C máxima", "QC ajuste"),2):
        wb["Calibration"].cell(i,9,label)
    from .calculations import groups
    for i, ((kind,sid,bio),_) in enumerate(groups(rows,{"sample","control"}).items(),2):
        wb["Results"].cell(i,9,p["result_unit"] if kind=="sample" else "% recuperación")
    readme = [
        ("Experimento",experiment_id), ("Estado",p["status"]), ("Fuente",p["source"]),
        ("Unidad resultado",p["result_unit"]), ("Base de masa",p["mass_basis"]),
        ("Edición","Editar SOLO RAW y valores numéricos Parameters; guardar y cerrar Excel. Actualizar desde la app."),
        ("Filas nuevas","Añadir filas RAW completas; Actualizar regenera fórmulas, grupos y gráficas con todos los registros."),
        ("Autoridad","Excel calcula; Origin importa resultados. Python no recalcula resultados de producción."),
        ("Blancos","blank: A_end-A_initial o A_end. Se resta la media global del blanco UNA vez. Un lote por experimento."),
        ("Blanco matriz","matrix_blank_delta: corrección ADICIONAL neta, tras su propio blanco/tiempo inicial. Introducir 0 explícito si no aplica."),
        ("Controles","expected y concentration en unidades del eje calibración. Recuperación = C interpolada / expected *100."),
        ("Réplicas","Una fila por lectura. bio_id identifica unidad independiente/extracción; tech_id lectura dentro de esa unidad."),
        ("Calibración","OLS con intercepto libre, medias por nivel, igual peso por nivel. No se elimina ningún punto automáticamente."),
        ("QC",p["qc_policy"]), ("DE no estimable","#N/A deliberado cuando n<2 o CV con media cero; no es cero."),
        ("Regeneración","Las hojas derivadas son gestionadas por la app y se regeneran. Antes de actualizar se conserva el libro completo en history."),
        ("Trazabilidad","RAW inicial y protocolo con hash conservados; cada actualización archiva inputs efectivos, libro y exports por ejecución."),
        ("Limitaciones","Sin validación química; sin corrección cinética avanzada, ponderación, incertidumbre metrológica o prueba estadística."),
    ]
    for values in readme:
        wb["ReadMe"].append(values)
    for ws in wb:
        ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
        ws.sheet_view.showGridLines=False
        ws.row_dimensions[1].height=36
        for cell in ws[1]:
            cell.font=Font(name="Calibri",size=11,bold=True,color="FFFFFF")
            cell.fill=PatternFill("solid",fgColor="173E4A")
            cell.alignment=Alignment(wrap_text=True,vertical="center")
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                editable=ws.title=="RAW" or (ws.title=="Parameters" and cell.column==2)
                cell.font=Font(name="Calibri",size=11,color="145B9B" if editable else "26373D")
                cell.fill=PatternFill("solid",fgColor="EAF4FC" if editable else ("F2F5F5" if cell.row%2==0 else "FFFFFF"))
                cell.protection=Protection(locked=not editable)
                cell.alignment=Alignment(vertical="top",wrap_text=True)
                if isinstance(cell.value,(int,float)) or cell.data_type=="f":
                    cell.number_format="0.0000"
            ws.row_dimensions[row[0].row].height=30
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=21
        ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.page_setup.orientation="landscape"; ws.page_setup.paperSize=ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=0
    wb["ReadMe"].column_dimensions["A"].width=26; wb["ReadMe"].column_dimensions["B"].width=110
    for r in range(2,wb["ReadMe"].max_row+1): wb["ReadMe"].row_dimensions[r].height=45
    wb["Parameters"].column_dimensions["A"].width=30; wb["Parameters"].column_dimensions["B"].width=105
    for r in range(2,wb["Parameters"].max_row+1): wb["Parameters"].row_dimensions[r].height=42
    wb["RAW"].column_dimensions["N"].width=58
    wb["Results"].column_dimensions["H"].width=28
    ws=wb["RAW"]
    dv=DataValidation(type="list",formula1='"blank,standard,control,sample"');dv.errorTitle="Tipo inválido";dv.error="Seleccionar tipo";dv.showErrorMessage=True
    ws.add_data_validation(dv);dv.add("B2:B10001")
    for col in ("J","K","L"):
        dv=DataValidation(type="decimal",operator="greaterThan",formula1=0,allow_blank=True)
        dv.showErrorMessage=True;ws.add_data_validation(dv);dv.add(f"{col}2:{col}10001")
    for col in ("F","M"):
        dv=DataValidation(type="decimal",operator="greaterThanOrEqual",formula1=0,allow_blank=True)
        dv.showErrorMessage=True;ws.add_data_validation(dv);dv.add(f"{col}2:{col}10001")
    cal=wb["Calibration"]
    xlabel,ylabel,resultlabel=axis_labels(p)
    chart=ScatterChart();chart.title="FRAP calibration";chart.x_axis.title=xlabel;chart.y_axis.title=ylabel
    last=max(2,len(groups(rows,{"standard"}))+1)
    observed=Series(Reference(cal,min_col=2,min_row=2,max_row=last),Reference(cal,min_col=1,min_row=2,max_row=last),title="Calibration means ± SD")
    observed.marker.symbol="circle";observed.marker.size=6;observed.graphicalProperties.line.noFill=True
    chart.series.append(observed)
    from openpyxl.chart.error_bar import ErrorBars
    from openpyxl.chart.data_source import NumDataSource,NumRef
    sd=NumDataSource(numRef=NumRef(f=f"Calibration!$D$2:$D${last}"))
    observed.errBars=ErrorBars(errDir='y',errBarType='both',errValType='cust',plus=sd,minus=sd)
    observed.marker.graphicalProperties.solidFill='0072B2'
    fit=Series(Reference(cal,min_col=5,min_row=2,max_row=last),Reference(cal,min_col=1,min_row=2,max_row=last),title="OLS fit")
    fit.graphicalProperties.line.solidFill='D55E00';fit.graphicalProperties.line.width=18000;chart.series.append(fit)
    chart.x_axis.majorGridlines=None;chart.y_axis.majorGridlines=None
    chart.x_axis.delete=False;chart.y_axis.delete=False
    chart.x_axis.tickLblPos="nextTo";chart.y_axis.tickLblPos="nextTo";chart.legend.position="b";chart.legend.overlay=False
    chart.width=22;chart.height=12;cal.add_chart(chart,"A12")
    summary=wb["Summary"]
    if summary.max_row>1:
        chart=BarChart();chart.title="FRAP · biological mean ± SD";chart.y_axis.title=resultlabel;chart.x_axis.title='Sample'
        chart.add_data(Reference(summary,min_col=3,min_row=1,max_row=summary.max_row),titles_from_data=True)
        chart.set_categories(Reference(summary,min_col=1,min_row=2,max_row=summary.max_row))
        sd=NumDataSource(numRef=NumRef(f"Summary!$D$2:$D${summary.max_row}"))
        chart.series[0].errBars=ErrorBars(errDir='y',errBarType='both',errValType='cust',plus=sd,minus=sd)
        chart.series[0].graphicalProperties.solidFill='B5D5E5'
        chart.series[0].graphicalProperties.line.solidFill='0072B2'
        chart.x_axis.majorGridlines=None;chart.y_axis.majorGridlines=None
        chart.x_axis.delete=False;chart.y_axis.delete=False
        chart.x_axis.tickLblPos="nextTo";chart.y_axis.tickLblPos="nextTo";chart.legend=None
        chart.width=22;chart.height=12;summary.add_chart(chart,"A7")
    wb.calculation=CalcProperties(calcId=0,fullCalcOnLoad=True)
    wb.save(path); wb.close()

def read_inputs(path):
    wb=load_workbook(path,data_only=False)
    try:
        if [x.value for x in wb["RAW"][1]] not in (COLUMNS,COLUMNS[:14]):
            raise ValueError("No cambiar nombres ni orden de columnas RAW")
        rows=[]
        for values in wb["RAW"].iter_rows(min_row=2,values_only=True):
            rows.append(dict(zip(COLUMNS,values)))
        p={r[0]:r[1] for r in wb["Parameters"].iter_rows(min_row=2,values_only=True) if r[0]}
        # Reject formulas in inputs: no stale caches and no untracked input dependencies.
        for ws in (wb["RAW"],wb["Parameters"]):
            for row in ws:
                if any(c.data_type=="f" for c in row):
                    raise ValueError("Entradas RAW/Parameters deben ser valores, no fórmulas")
        return normalize(rows,validate(p)),p
    finally:
        wb.close()

def recalculate(path, pdf=None, previews=None):
    """Dedicated Excel instance; never attaches to or closes user's Excel session."""
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    app=None; book=None
    try:
        app=win32com.client.DispatchEx("Excel.Application")
        app.Visible=False;app.DisplayAlerts=False;app.AskToUpdateLinks=False
        app.AutomationSecurity=3
        book=app.Workbooks.Open(str(Path(path).resolve()),UpdateLinks=0,ReadOnly=False)
        if book.ReadOnly: raise RuntimeError("Excel abrió el archivo en solo lectura; cerrar el libro y reintentar")
        app.CalculateFullRebuild()
        deadline=time.monotonic()+90
        while app.CalculationState != 0:
            if time.monotonic()>deadline: raise TimeoutError("Excel no termina de recalcular")
            pythoncom.PumpWaitingMessages();time.sleep(0.1)
        # Native chart layout gives tick labels, units and legend separate space.
        for name in ("Summary","Calibration"):
            sheet=book.Worksheets(name)
            for index in range(1,sheet.ChartObjects().Count+1):
                obj=sheet.ChartObjects(index);chart=obj.Chart
                sheet.Activate();obj.Activate()
                chart.Axes(1).TickLabels.NumberFormat="General"
                chart.Axes(2).TickLabels.NumberFormat="General"
                # Some Excel builds reject manual PlotArea geometry for imported charts.
                # Label positions alone remain independent of that optional geometry.
                if chart.Axes(2).HasTitle:
                    unit=chart.Axes(2).AxisTitle.Text
                    chart.Axes(2).HasTitle=False
                    chart.ChartTitle.Text="FRAP | "+unit
                if chart.Axes(1).HasTitle:chart.Axes(1).AxisTitle.Top=obj.Height-40
                if chart.HasLegend:chart.Legend.Top=obj.Height-23
        book.Save()
        if pdf:
            book.Worksheets("Summary").ExportAsFixedFormat(0,str(Path(pdf).resolve()))
        if previews:
            Path(previews).mkdir(parents=True,exist_ok=True)
            for name in ("Summary","Calibration"):
                sheet=book.Worksheets(name)
                for index in range(1,sheet.ChartObjects().Count+1):
                    sheet.ChartObjects(index).Chart.Export(str(Path(previews).resolve()/f"excel_{name}_{index}.png"))
    finally:
        if book is not None: book.Close(SaveChanges=False)
        if app is not None: app.Quit()
        pythoncom.CoUninitialize()

from contextvars import ContextVar
from functools import wraps
_value_cache=ContextVar('excel_value_cache',default=None)

def value_session(function):
    """Share one immutable read of saved Excel caches within one operation only."""
    @wraps(function)
    def wrapped(*args,**kwargs):
        token=_value_cache.set({})
        try:return function(*args,**kwargs)
        finally:_value_cache.reset(token)
    return wrapped

def _value_key(path):
    path=Path(path).resolve();stat=path.stat()
    return (str(path),stat.st_mtime_ns,stat.st_size)

def share_values(source,destination):
    """Caller has copied identical bytes; reuse the already parsed snapshot."""
    cache=_value_cache.get()
    if cache is not None and _value_key(source) in cache:cache[_value_key(destination)]=cache[_value_key(source)]

def values(path,sheet):
    cache=_value_cache.get();key=_value_key(path)
    if cache is not None:
        if key not in cache:
            wb=load_workbook(path,data_only=True,read_only=True)
            try:cache[key]={ws.title:list(ws.values) for ws in wb}
            finally:wb.close()
        return cache[key][sheet]
    wb=load_workbook(path,data_only=True,read_only=True)
    try:return list(wb[sheet].values)
    finally:wb.close()
