"""Create the exact onedir payload accepted by the PhDexLab updater (no user data)."""
import argparse,hashlib,importlib.metadata as metadata,json,shutil,sys,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from phdexlab import __version__
from phdexlab.updater import REPOSITORY

def package(application,output):
    application=Path(application).resolve();output=Path(output).resolve()
    if not (application/'PhDexLab.exe').is_file():raise ValueError('Build Application first')
    notices=application/'THIRD_PARTY_LICENSES';notices.mkdir(exist_ok=True)
    for file in [ROOT/'LICENSE',ROOT/'THIRD_PARTY_NOTICES.md',*sorted((ROOT/'licenses').glob('*.txt'))]:shutil.copy2(file,notices/file.name)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.exists():shutil.copy2(python_license,notices/'Python-LICENSE.txt')
    dependencies=['PySide6-Essentials','shiboken6','openpyxl','matplotlib','SciencePlots','originpro','OriginExt','pywin32','numpy','Pillow','contourpy','cycler','fonttools','kiwisolver','packaging','pyparsing','python-dateutil','six','PyInstaller','altgraph']
    inventory={}
    for name in dependencies:
        try:dist=metadata.distribution(name)
        except metadata.PackageNotFoundError:continue
        inventory[name]=dist.version
        dest=notices/name;dest.mkdir(exist_ok=True)
        # Record licences from distributions, not local install metadata or absolute paths.
        for entry in dist.files or []:
            parts=Path(str(entry)).parts
            if not any(part.endswith('.dist-info') for part in parts):continue
            if 'licenses' in parts or any(word in Path(str(entry)).name.lower() for word in ('license','copying','notice')):
                source=Path(dist.locate_file(entry))
                if source.is_file():
                    index=next(i for i,part in enumerate(parts) if part.endswith('.dist-info'));rel=Path(*parts[index+1:]);target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (notices/'dependencies.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    candidates=[p for p in application.rglob('*') if p.is_file()]
    files=[]
    for path in sorted(candidates):
        rel=path.relative_to(application)
        if any(part in ('__pycache__','.git') for part in rel.parts) or path.name in ('startup-error.log',):continue
        if path.is_symlink():raise ValueError('Links cannot be packaged')
        files.append(path)
    hashes={'Application/'+p.relative_to(application).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    manifest=dict(schema=1,repository=REPOSITORY,version=__version__,files=hashes)
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in files:z.write(path,'Application/'+path.relative_to(application).as_posix())
        z.writestr('release.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(output) as z:
        if z.testzip():raise ValueError('Archive verification failed')
    checksum=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name('SHA256SUMS.txt').write_text(checksum+'  '+output.name+'\n',encoding='utf-8')
    print(json.dumps(dict(version=__version__,file=output.name,sha256=checksum,files=len(files),bytes=output.stat().st_size)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--application',default=ROOT/'Application');parser.add_argument('--output',default=ROOT.parent/'PhDexLab-Windows-x64.zip');args=parser.parse_args();package(args.application,args.output)
