"""Public API for a future PhDex adapter. No dependency on PhDex itself."""
import contextlib
import csv
import hashlib
import json
import os
import shutil
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from . import __version__
from .protocols import FE, canonical, digest, validate
from .data_entry import normalize
from .excel import write_book, read_inputs, recalculate, values
from .paths import Layout,migrate_legacy

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(canonical(value),encoding="utf-8")
    # Windows readers/antivirus may briefly deny replacement of an open status file.
    for attempt in range(10):
        try:os.replace(tmp,path);break
        except PermissionError:
            if attempt==9:raise
            time.sleep(0.05)

def audit(folder,event,**details):
    path=Layout(folder).meta/"audit.jsonl"
    previous=""
    if path.exists():
        lines=path.read_text(encoding="utf-8").splitlines()
        if lines: previous=json.loads(lines[-1])["hash"]
    entry=dict(time=datetime.now(timezone.utc).isoformat(),event=event,previous=previous,**details)
    entry["hash"]=digest(entry)
    with path.open("a",encoding="utf-8") as f: f.write(canonical(entry)+"\n")

def verify(folder):
    folder=Layout(folder).meta;m=json.loads((folder/"experiment.json").read_text(encoding="utf-8"))
    for name,key in (("protocol.initial.json","protocol_hash"),("raw.initial.json","raw_hash")):
        if digest(json.loads((folder/name).read_text(encoding="utf-8")))!=m[key]:
            raise ValueError(f"Snapshot inicial alterado: {name}")
    previous=""
    for line in (folder/"audit.jsonl").read_text(encoding="utf-8").splitlines():
        entry=json.loads(line);signature=entry.pop("hash")
        if entry["previous"]!=previous or digest(entry)!=signature:
            raise ValueError("Cadena de auditoría alterada")
        previous=signature
    for path in (folder/"revisions").glob("*.json"):
        if digest(json.loads(path.read_text(encoding="utf-8")))!=path.stem:
            raise ValueError(f"Revisión alterada: {path.name}")
    return m

@contextlib.contextmanager
def locked(folder):
    meta=Layout(folder).meta;meta.mkdir(parents=True,exist_ok=True);lock=meta/".workflow.lock"
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: raise RuntimeError("Experimento en uso. Si hubo un cierre inesperado, comprobar procesos y retirar .workflow.lock.")
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd);yield
    finally: lock.unlink(missing_ok=True)

def preflight(rows,p):
    rows=normalize(rows,validate(p))
    if not any(d["kind"]=="blank" for d in rows): raise ValueError("Se necesita al menos un blanco de reactivos")
    standards=[d for d in rows if d["kind"]=="standard"]
    concentrations={d["concentration"] for d in standards}
    if len(concentrations)<3: raise ValueError("Se requieren al menos 3 concentraciones distintas de calibración")
    sid_by_c={}
    for d in standards:
        group=(d["sample_id"],d["bio_id"])
        c=d["concentration"]
        if c in sid_by_c and sid_by_c[c]!=group:
            raise ValueError("Cada concentración debe tener un único ID de nivel; distinguir réplicas con tech_id")
        sid_by_c[c]=group
    return rows

def create_experiment(folder,rows,protocol=None):
    folder=Path(folder).resolve();p=dict(protocol or FE);rows=preflight(rows,p)
    if folder.exists() and any(folder.iterdir()): raise FileExistsError("Elegir una carpeta nueva o vacía")
    folder.mkdir(parents=True,exist_ok=True)
    layout=Layout(folder);layout.prepare();meta=layout.meta
    m=dict(schema=2,file_stem=folder.name,app_version=__version__,experiment_id=str(uuid.uuid4()),
           created=datetime.now(timezone.utc).isoformat(),protocol_hash=digest(p),raw_hash=digest(rows))
    dump(meta/"experiment.json",m);dump(meta/"protocol.initial.json",p);dump(meta/"raw.initial.json",rows)
    dump(meta/"revisions"/(digest(p)+".json"),p)
    write_book(layout.master,rows,p,m["experiment_id"])
    audit(folder,"created",workbook_sha256=file_hash(layout.master),raw_hash=digest(rows),protocol_hash=digest(p))
    dump(meta/"status.json",dict(state="pending",message="Pendiente de recálculo nativo Excel y actualización Origin"))
    return folder

def refresh(folder, origin_mode="connector", edited_rows=None, edited_protocol=None, expected_hash=None, progress=None):
    manifest=Layout(folder).meta/'experiment.json'
    if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8')).get('schema')==3:
        from .experiments import refresh as refresh_multi
        return refresh_multi(folder,origin_mode,edited_rows,edited_protocol,expected_hash,progress)
    notify=progress or (lambda *args,**kwargs:None)
    notify(1,"Verificando datos y trazabilidad")
    folder=Path(folder).resolve()
    verify(folder)
    layout=migrate_legacy(folder);layout.prepare();meta=layout.meta
    with locked(folder):
        m=verify(folder);master=layout.master
        before=file_hash(master)
        if expected_hash and expected_hash!=before:
            raise RuntimeError("El Excel cambió desde que se abrió la ventana. Reabrir para cargar la versión guardada.")
        rows,p=read_inputs(master)
        if edited_rows is not None: rows=edited_rows
        if edited_protocol is not None: p=edited_protocol
        rows=preflight(rows,p)
        # Protocol input structure fixed for v0.1; unknown fields cannot change equation behavior silently.
        initial=json.loads((meta/"protocol.initial.json").read_text(encoding="utf-8"))
        if set(p)!=set(initial): raise ValueError("No añadir ni borrar claves de protocolo en este prototipo")
        run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        history=layout.history/run_id;history.mkdir()
        shutil.copy2(master,history/"master.before.xlsx")
        if layout.project.exists(): shutil.copy2(layout.project,history/"analysis.before.opju")
        dump(history/"inputs.json",dict(rows=rows,protocol=p,source_sha256=before))
        revision=meta/"revisions"/(digest(p)+".json")
        if not revision.exists(): dump(revision,p)
        staged=history/"master.calculated.xlsx"
        report=dict(state="running",run=run_id,origin_mode=origin_mode,protocol_hash=digest(p),raw_hash=digest(rows))
        dump(meta/"status.json",report)
        audit(folder,"refresh_started",**report)
        try:
            notify(2,"Generando fórmulas y recalculando en Excel")
            write_book(staged,rows,p,m["experiment_id"])
            recalculate(staged,pdf=history/"excel_summary.pdf",previews=history)
            notify(3,"Comprobando resultados y exportando Excel")
            # Missing caches or broken formulas must never masquerade as exported results.
            for sheet in ("Calibration","Results","Summary","Processing"):
                data=values(staged,sheet)
                for row in data[1:]:
                    for v in row:
                        if isinstance(v,str) and v.startswith(("#REF!","#DIV/0!","#VALUE!","#NAME?","#NUM!","#NULL!")):
                            raise ValueError(f"Error de cálculo en {sheet}: {v}")
            cal=values(staged,"Calibration")
            if not isinstance(cal[2][9],(int,float)) or cal[2][9]<=0:
                raise ValueError("Calibración FRAP con pendiente no positiva o sin caché; revisar RAW")
            if file_hash(master)!=before: raise RuntimeError("El Excel se modificó durante la actualización; no se sobrescribe")
            replacement=layout.documents/(layout.stem+".next.xlsx");shutil.copy2(staged,replacement);os.replace(replacement,master)
            # Clear old outputs before publishing this run: never present stale images as current.
            for old in layout.generated():
                relative=old.relative_to(folder);target=history/"previous"/relative;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.move(str(old),str(target))
            shutil.copy2(history/"excel_summary.pdf",layout.figures/"Excel"/(layout.stem+"_summary.pdf"))
            for image in history.glob("excel_*.png"): shutil.copy2(image,layout.figures/"Excel"/(layout.stem+"_"+image.name))
            for sheet in ("Results","Summary","Calibration"):
                with (layout.results/(layout.stem+"_"+sheet.lower()+".csv")).open("w",encoding="utf-8-sig",newline="") as f:
                    csv.writer(f).writerows(values(master,sheet))
            report.update(state="excel_ready",excel_sha256=file_hash(master))
            notify(4,"Actualizando Origin y exportando gráficas" if origin_mode!="none" else "Origin omitido: modo solo Excel")
            if origin_mode!="none":
                try:
                    from .origin import sync
                    report["origin"]=sync(folder,origin_mode)
                    report["state"]="complete" if not report["origin"]["errors"] else "partial"
                except Exception as e:
                    report.update(state="partial",origin_error=f"{type(e).__name__}: {e}")
                    dump(meta/"origin_status.json",dict(state="failed",error=report["origin_error"],run=run_id))
            else: report["origin"]={"state":"skipped"}
            notify(5,"Preparando figuras científicas")
            from .publication import export_publication
            report['publication']=export_publication(folder)
            notify(6,"Archivando resultados y auditoría")
            report["outputs"]={str(f.relative_to(folder)):file_hash(f) for f in layout.generated()}
            for output in layout.generated():
                target=history/"outputs"/output.relative_to(folder);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(output,target)
            if layout.project.exists(): shutil.copy2(layout.project,history/"analysis.after.opju")
            dump(history/"report.json",report);dump(meta/"status.json",report)
            audit(folder,"refresh_finished",**report)
            return report
        except Exception as e:
            report.update(state="failed",error=f"{type(e).__name__}: {e}")
            dump(history/"report.json",report);dump(meta/"status.json",report)
            audit(folder,"refresh_failed",**report)
            raise
