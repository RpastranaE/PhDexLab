"""Worker process keeps the GUI responsive and COM isolated."""
import json
import sys
from pathlib import Path
from .experiments import refresh
from .integration import dump
from .paths import Layout

def run(args=None):
    values=list(args if args is not None else sys.argv[1:4])
    folder,mode=values[:2];payload=values[2] if len(values)>2 else ''
    kwargs={}
    if payload:
        data=json.loads(Path(payload).read_text(encoding="utf-8"))
        if data.get('force'):kwargs=dict(force=True)
        else:kwargs=dict(edited_assays=data["assays"],expected_hash=data["expected_hash"]) if "assays" in data else dict(edited_rows=data["rows"],edited_protocol=data["protocol"],expected_hash=data["expected_hash"])
    def progress(step,label,**extra):
        try:dump(Layout(folder).meta/'progress.json',dict(dict(step=step,total=6,label=label,busy=True),**extra))
        except OSError as error:print(f'Progress update skipped: {error}',file=sys.stderr,flush=True)
    try:
        report=refresh(folder,mode,progress=progress,**kwargs)
        progress(6,'Sin cambios: Excel, Origin y exportaciones verificados' if report.get('reused') else 'Actualización finalizada',busy=False,state=report['state'])
        print(json.dumps(report,indent=2,ensure_ascii=True))
    except Exception as error:
        from .file_access import WorkbookInUseError,EXCEL_IN_USE
        progress(0,EXCEL_IN_USE if isinstance(error,WorkbookInUseError) else 'Error: consultar registro',busy=False,state='failed')
        raise
    if payload:Path(payload).unlink(missing_ok=True)

if __name__=='__main__':run()
