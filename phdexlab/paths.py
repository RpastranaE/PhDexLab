"""Experiment layout v2. User documents and figures are separate from technical state."""
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import zipfile

@dataclass(frozen=True)
class Layout:
    root: Path

    def __post_init__(self):object.__setattr__(self,'root',Path(self.root).resolve())
    @property
    def legacy(self):return not (self.root/'_internal'/'experiment.json').exists() and (self.root/'experiment.json').exists()
    @property
    def meta(self):return self.root if self.legacy else self.root/'_internal'
    @property
    def stem(self):
        manifest=self.meta/'experiment.json'
        if manifest.exists():return json.loads(manifest.read_text(encoding='utf-8')).get('file_stem',self.root.name)
        return self.root.name
    @property
    def documents(self):return self.root/'Documents'
    @property
    def master(self):return self.root/'master.xlsx' if self.legacy else self.documents/(self.stem+'.xlsx')
    @property
    def project(self):return self.root/'analysis.opju' if self.legacy else self.documents/(self.stem+'.opju')
    @property
    def figures(self):return self.root/'Figures'
    @property
    def results(self):return self.root/'Results'
    @property
    def history(self):return self.meta/'history'
    def origin_figures(self,extension):return self.figures/'Origin'/extension.upper()
    def prepare(self):
        manifest=self.meta/'experiment.json'
        multi=manifest.exists() and json.loads(manifest.read_text(encoding='utf-8')).get('schema')==3
        if multi:
            for path in (self.meta,self.meta/'revisions',self.history,self.documents,self.results,self.figures):path.mkdir(parents=True,exist_ok=True)
            return
        for p in (self.meta,self.meta/'revisions',self.history,self.documents,self.results,self.figures/'Excel',self.figures/'Publication'):
            p.mkdir(parents=True,exist_ok=True)
        for ext in ('png','pdf','svg'):self.origin_figures(ext).mkdir(parents=True,exist_ok=True)
    def generated(self):
        return [p for parent in (self.figures,self.results) if parent.exists() for p in parent.rglob('*') if p.is_file() and p.name.startswith(self.stem+'_')]

def migrate_legacy(folder):
    """Lossless on-disk migration; archive original bytes before moving legacy files."""
    old=Layout(folder)
    if not old.legacy:return old
    if (old.root/'.workflow.lock').exists():raise RuntimeError('Cerrar la actualización activa antes de reorganizar el experimento')
    meta=old.root/'_internal';meta.mkdir(exist_ok=True)
    archive=meta/'migration_v1_backup.zip'
    if not archive.exists():
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for file in old.root.rglob('*'):
                if file.is_file() and not file.is_relative_to(meta):z.write(file,file.relative_to(old.root))
    manifest=json.loads((old.root/'experiment.json').read_text(encoding='utf-8'))
    # Fixed descendants only; every move is kept inside this experiment's resolved root.
    destinations={name:meta/name for name in ('protocol.initial.json','raw.initial.json','audit.jsonl','status.json','origin_status.json','revisions','history')}
    for name,target in destinations.items():
        source=old.root/name
        assert source.resolve().is_relative_to(old.root) and target.resolve().is_relative_to(old.root)
        if source.exists() and not target.exists():shutil.move(str(source),str(target))
    manifest.update(schema=2,file_stem=old.root.name)
    (meta/'experiment.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True),encoding='utf-8')
    new=Layout(old.root);new.prepare()
    for source,target in ((old.root/'master.xlsx',new.master),(old.root/'analysis.opju',new.project)):
        if source.exists() and not target.exists():shutil.move(str(source),str(target))
    if (old.root/'exports').exists():
        target=meta/'legacy_exports'
        if not target.exists():shutil.move(str(old.root/'exports'),str(target))
    # The original manifest is preserved inside the migration archive.
    (old.root/'experiment.json').unlink()
    return new
