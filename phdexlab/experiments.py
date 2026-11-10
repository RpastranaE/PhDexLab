"""Experiment-level API: one master workbook, independently staged assays, one Origin project."""
import copy,json,os,shutil,uuid
from datetime import datetime,timezone
from pathlib import Path
from . import __version__
from .integration import dump,audit,verify,locked,file_hash
from .paths import Layout,migrate_legacy
from .protocols import digest
from .multi_excel import write_master,read_master,validate_ids,sheet_name,recalculate_master
from .assay_engine import state,engine
from .excel import values,value_session,share_values
import time

def config(assays):return [{k:v for k,v in a.items() if k!='rows'} for a in assays]
def raw(assays):return [dict(id=a['id'],rows=a.get('rows',[])) for a in assays]
def new_id(assays,method,minimum=1):
    number=max(minimum,max([int(a['id'].split('_')[0][1:]) for a in assays]+[0])+1)
    return f'A{number:02}_{method[:12]}'

def create(folder,assays,excel_style=None):
    folder=Path(folder).resolve();validate_ids(assays)
    if not assays:raise ValueError('Añadir al menos un ensayo')
    if folder.exists() and any(folder.iterdir()):raise FileExistsError('Elegir una carpeta nueva o vacía')
    folder.mkdir(parents=True,exist_ok=True);l=Layout(folder);l.meta.mkdir(exist_ok=True)
    m=dict(schema=3,file_stem=folder.name,app_version=__version__,experiment_id=str(uuid.uuid4()),created=datetime.now(timezone.utc).isoformat(),protocol_hash=digest(config(assays)),raw_hash=digest(raw(assays)))
    m['next_assay_number']=max(int(a['id'].split('_')[0][1:]) for a in assays)+1
    dump(l.meta/'experiment.json',m);l.prepare();dump(l.meta/'protocol.initial.json',config(assays));dump(l.meta/'raw.initial.json',raw(assays))
    for a in assays:dump(l.meta/'revisions'/(digest(a['protocol'])+'.json'),a['protocol'])
    from .excel_styles import save as save_excel_style
    if excel_style is not None:save_excel_style(folder,excel_style)
    states=write_master(l.master,assays,m['experiment_id'],excel_style=excel_style);audit(folder,'created_multi',workbook_sha256=file_hash(l.master),assays=config(assays))
    dump(l.meta/'status.json',dict(state='draft' if any(s['state']=='draft' for s in states.values()) else 'pending',assays=states));return folder

def read(folder):
    verify(folder);l=migrate_legacy(folder);return read_master(l.master)

def revision(l,assays):
    for a in assays:
        path=l.meta/'revisions'/(digest(a['protocol'])+'.json')
        if not path.exists():dump(path,a['protocol'])

def archive(l):
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');history=l.history/run;history.mkdir(parents=True)
    shutil.copy2(l.master,history/(l.stem+'.before.xlsx'))
    if l.project.exists():shutil.copy2(l.project,history/(l.stem+'.before.opju'))
    return run,history

def save(folder,assays,expected_hash,excel_style=None):
    verify(folder);l=migrate_legacy(folder);validate_ids(assays)
    with locked(folder):
        if expected_hash and expected_hash!=file_hash(l.master):raise RuntimeError('El Excel cambió desde que se abrió la ventana. Reabrir antes de guardar.')
        from .excel_styles import read as read_excel_style,save as save_excel_style
        selected_style=read_excel_style(folder) if excel_style is None else excel_style
        run,h=archive(l);m=verify(folder);staged=h/(l.stem+'.draft.xlsx');states=write_master(staged,assays,m['experiment_id'],excel_style=selected_style)
        if excel_style is not None:save_excel_style(folder,excel_style)
        replacement=l.documents/(l.stem+'.next.xlsx');shutil.copy2(staged,replacement);os.replace(replacement,l.master)
        m.update(schema=3,app_version=__version__,next_assay_number=max(m.get('next_assay_number',1),max(int(a['id'].split('_')[0][1:]) for a in assays)+1));dump(l.meta/'experiment.json',m);revision(l,assays)
        # Results are invalidated immediately when inputs change; archive them, never leave stale figures current.
        for old in l.generated():
            target=h/'previous'/old.relative_to(l.root);target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(old),str(target))
        audit(folder,'saved_inputs',run=run,assays=config(assays),raw_hash=digest(raw(assays)),workbook_sha256=file_hash(l.master))
        dump(l.meta/'status.json',dict(state='draft' if any(s['state']=='draft' for s in states.values()) else 'pending',assays=states));return states

@value_session
def refresh(folder,origin_mode='connector',edited_rows=None,edited_protocol=None,expected_hash=None,progress=None,edited_assays=None,force=False):
    started=time.perf_counter();timings={};last=[started,1]
    def notify(step,label):
        now=time.perf_counter()
        if step!=last[1]:timings[str(last[1])]=round(now-last[0],4);last[:]=[now,step]
        if progress:progress(step,label)
    notify(1,'Verificando ensayos y trazabilidad')
    verify(folder);l=migrate_legacy(folder);l.prepare()
    with locked(folder):
        from .file_access import assert_available
        assert_available(l.master)
        before=file_hash(l.master)
        if expected_hash and expected_hash!=before:raise RuntimeError('El Excel cambió desde que se abrió la ventana. Reabrir antes de actualizar.')
        from .graph_styles import presentation_hash
        style_hash=presentation_hash(folder)
        from .excel_styles import read as read_excel_style
        excel_style=read_excel_style(folder);excel_style_hash=digest(excel_style)
        previous=l.meta/'status.json'
        if not force and edited_assays is None and edited_rows is None and edited_protocol is None and previous.exists():
            old=json.loads(previous.read_text(encoding='utf-8'))
            if (old.get('state')=='complete' and old.get('app_version')==__version__ and old.get('origin_mode')==origin_mode
                and old.get('excel_style_hash')==excel_style_hash and old.get('excel_sha256')==before and old.get('presentation_hash')==style_hash
                and (origin_mode=='none' or old.get('origin',{}).get('master_path')==str(l.master))
                and (origin_mode=='none' or (l.project.exists() and old.get('project_sha256')==file_hash(l.project)))
                and old.get('outputs') and all((l.root/name).is_file() and file_hash(l.root/name)==sha for name,sha in old['outputs'].items())):
                notify(6,'Sin cambios: Excel, Origin y exportaciones verificados')
                old=dict(old,reused=True,verification_seconds=round(time.perf_counter()-started,4));dump(previous,old);audit(folder,'refresh_reused',excel_sha256=before,seconds=old['verification_seconds']);return old
        assays=copy.deepcopy(edited_assays) if edited_assays is not None else read_master(l.master)
        if edited_rows is not None:assays[0]['rows']=edited_rows
        if edited_protocol is not None:assays[0]['protocol']=edited_protocol
        validate_ids(assays);m=verify(folder);run,h=archive(l)
        dump(h/'inputs.json',dict(assays=assays,source_sha256=before));revision(l,assays)
        report=dict(state='running',run=run,origin_mode=origin_mode,assays={},force_rebuild=force,reused=False);dump(l.meta/'status.json',report);audit(folder,'refresh_started_multi',run=run)
        try:
            notify(2,'Preparando el Excel maestro y calculando los ensayos completos')
            staged=h/(l.stem+'.calculated.xlsx');report['assays']=write_master(staged,assays,m['experiment_id'],calculated=True,excel_style=excel_style)
            ready=[a for a in assays if report['assays'][a['id']]['state']=='ready']
            pdfs=recalculate_master(staged,h/'Excel') if ready else []
            notify(3,'Comprobando resultados y separando exportaciones por ensayo')
            for a in ready:
                status=report['assays'][a['id']];errors=[]
                for role in ('Processing','Results','Summary')+ (('Calibration',) if engine(a['protocol']) in ('colorimetric','inhibition') else ()):
                    for row in values(staged,sheet_name(a,role))[1:]:
                        errors.extend(v for v in row if isinstance(v,str) and v.startswith(('#DIV/0!','#VALUE!','#REF!','#NUM!','#NAME?','#NULL!')))
                if engine(a['protocol']) in ('colorimetric','inhibition'):
                    cal=values(staged,sheet_name(a,'Calibration'));slope=cal[2][9]
                    if not isinstance(slope,(int,float)) or slope<=0:errors.append('Calibración con pendiente no positiva o caché ausente')
                status.update(state='invalid' if errors else 'calculated',issue='; '.join(sorted(set(errors))))
                summ=values(staged,sheet_name(a,'Summary'))
                if not errors and any(row[2]=='#N/A' for row in summ[1:]):status.update(state='needs_review',issue='Hay unidades sin resultado: revisar EC50/mesetas/rango. No se eliminan del cálculo experimental.')
            if file_hash(l.master)!=before:raise RuntimeError('El Excel fue modificado durante el cálculo; no se sobrescribe')
            replacement=l.documents/(l.stem+'.next.xlsx');shutil.copy2(staged,replacement)
            assert_available(l.master)
            try:os.replace(replacement,l.master)
            except PermissionError as error:
                if getattr(error,'winerror',None) in (32,33):
                    from .file_access import WorkbookInUseError,EXCEL_IN_USE
                    raise WorkbookInUseError(EXCEL_IN_USE) from error
                raise
            share_values(staged,l.master)
            m.update(schema=3,app_version=__version__,next_assay_number=max(m.get('next_assay_number',1),max(int(a['id'].split('_')[0][1:]) for a in assays)+1));dump(l.meta/'experiment.json',m)
            for old in l.generated():
                target=h/'previous'/old.relative_to(l.root);target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(old),str(target))
            import csv
            for a in assays:
                target=l.results/a['id'];target.mkdir(parents=True,exist_ok=True)
                for role in ('Results','Summary'):
                    with (target/(l.stem+'_'+a['id']+'_'+role.lower()+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(values(l.master,sheet_name(a,role)))
                pdf=next((p for p in pdfs if p.stem==sheet_name(a,'Summary')),None)
                if pdf:
                    target=l.figures/a['id']/'Excel';target.mkdir(parents=True,exist_ok=True);shutil.copy2(pdf,target/(l.stem+'_'+a['id']+'_summary.pdf'))
            notify(4,'Actualizando el proyecto Origin por carpetas de ensayo')
            if origin_mode!='none' and ready:
                try:
                    from .multi_origin import sync
                    report['origin']=sync(folder,assays,report['assays'],origin_mode,notify,force=force)
                except Exception as error:report['origin']=dict(errors=[f'{type(error).__name__}: {error}'])
            else:report['origin']=dict(state='skipped',errors=[])
            notify(5,'Exportando figuras científicas por metodología')
            from .multi_publication import export
            report['publication']=export(folder,assays,report['assays'],force=force)
            notify(6,'Archivando el experimento y sus revisiones')
            report['state']='complete' if all(s['state']=='calculated' for s in report['assays'].values()) and not report['origin'].get('errors') else 'partial' if ready else 'draft'
            report['excel_sha256']=file_hash(l.master);report['outputs']={str(f.relative_to(l.root)):file_hash(f) for f in l.generated()}
            report.update(app_version=__version__,presentation_hash=style_hash,excel_style_hash=excel_style_hash,project_sha256=file_hash(l.project) if l.project.exists() else None)
            for output in l.generated():
                target=h/'outputs'/output.relative_to(l.root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(output,target)
            if l.project.exists():shutil.copy2(l.project,h/(l.stem+'.after.opju'))
            timings['6']=round(time.perf_counter()-last[0],4);report['timings_seconds']=timings;report['total_seconds']=round(time.perf_counter()-started,4)
            dump(h/'report.json',report);dump(l.meta/'status.json',report);audit(folder,'refresh_finished_multi',**report);return report
        except Exception as error:
            report.update(state='failed',error=f'{type(error).__name__}: {error}');dump(h/'report.json',report);dump(l.meta/'status.json',report);audit(folder,'refresh_failed_multi',**report);raise
