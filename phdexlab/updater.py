"""Stable GitHub releases only. Verified archive -> isolated stage -> install on exit.

No tokens, experiment paths, or analytical data are sent to GitHub.
The update replaces Application only. This is integrity checking, not code signing.
"""
import hashlib,json,os,re,shutil,subprocess,sys,uuid,zipfile
from pathlib import Path,PurePosixPath
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError
from . import __version__
from .data_templates import user_data_dir

REPOSITORY='RpastranaE/PhDexLab'
REPO_URL='https://github.com/'+REPOSITORY
API_URL='https://api.github.com/repos/'+REPOSITORY+'/releases/latest'
ASSET_NAME='PhDexLab-Windows-x64.zip'
PUBLIC_METADATA=REPO_URL+'/releases/latest/download/latest.json'
MAX_ARCHIVE=600*1024*1024
MAX_EXPANDED=1800*1024*1024

def version(value):
    match=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)',str(value))
    if not match:raise ValueError('Expected a stable version: major.minor.patch')
    return tuple(map(int,match.groups()))

def settings():
    try:data=json.loads((user_data_dir()/'updates'/'settings.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):data={}
    return dict(automatic=data.get('automatic',True) is True)

def set_automatic(enabled):
    path=user_data_dir()/'updates'/'settings.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(automatic=bool(enabled))),encoding='utf-8')

def trusted_url(url,api=False):
    p=urlsplit(url)
    if p.scheme!='https' or p.username or p.password or p.port not in (None,443):raise ValueError('Untrusted update URL')
    if api:
        if url!=API_URL:raise ValueError('Untrusted API URL')
    elif p.hostname!='github.com' or not p.path.startswith('/'+REPOSITORY+'/releases/download/'):
        raise ValueError('Untrusted release asset')
    return url

def request(url,api=False):
    trusted_url(url,api);return Request(url,headers={'User-Agent':'PhDexLab/'+__version__,'Accept':'application/vnd.github+json' if api else 'application/octet-stream'})

def latest(opener=urlopen):
    try:return _api_latest(opener)
    except HTTPError as error:
        if error.code not in (403,429):raise
        # Anonymous API quota is shared on many laboratory networks. The same
        # public release carries its metadata as an HTTPS asset, without tokens.
        try:return _public_latest(opener)
        except Exception as fallback:
            raise RuntimeError('GitHub temporarily limited update checks. Please try again later or open the releases page.') from fallback

def _public_latest(opener):
    req=Request(PUBLIC_METADATA,headers={'User-Agent':'PhDexLab/'+__version__})
    with opener(req,timeout=20) as response:
        redirected=urlsplit(response.geturl())
        if redirected.scheme!='https' or redirected.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):
            raise ValueError('Untrusted metadata redirect')
        raw=response.read(65537)
        if len(raw)>65536:raise ValueError('Release metadata too large')
        data=json.loads(raw)
    if data.get('repository')!=REPOSITORY or data.get('schema')!=1:raise ValueError('Wrong release metadata')
    return _validate_release(data)

def _api_latest(opener):
    with opener(request(API_URL,True),timeout=20) as response:
        if urlsplit(response.geturl()).hostname!='api.github.com':raise ValueError('Unexpected API redirect')
        raw=response.read(2*1024*1024+1)
        if len(raw)>2*1024*1024:raise ValueError('Release response too large')
        data=json.loads(raw)
    return _validate_release(data)

def _validate_release(data):
    if data.get('draft') or data.get('prerelease'):raise ValueError('Release is not stable')
    tag=data['tag_name'];version(tag)
    if data.get('html_url')!=REPO_URL+'/releases/tag/'+tag:raise ValueError('Unexpected release repository')
    asset=next((a for a in data.get('assets',[]) if a.get('name')==ASSET_NAME),None)
    if asset is None:raise ValueError('No compatible Windows package in latest release')
    trusted_url(asset['browser_download_url'])
    if asset['browser_download_url']!=REPO_URL+'/releases/download/'+tag+'/'+ASSET_NAME:raise ValueError('Asset version mismatch')
    checksum=asset.get('digest') or ''
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',checksum):raise ValueError('Release has no SHA-256 digest; update refused')
    if type(asset.get('size')) is not int or not 0<asset['size']<=MAX_ARCHIVE:raise ValueError('Invalid update size')
    return dict(version=tag.lstrip('v'),url=data['html_url'],asset=asset,newer=version(tag)>version(__version__))

def download(release,path,progress=lambda *args:None,opener=urlopen,cancel=lambda:False):
    asset=release['asset'];sha=hashlib.sha256();total=0;path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    try:
        with opener(request(asset['browser_download_url']),timeout=30) as response,path.open('wb') as out:
            redirected=urlsplit(response.geturl())
            if redirected.scheme!='https' or redirected.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):raise ValueError('Untrusted download redirect')
            while True:
                if cancel():raise InterruptedError('Update download cancelled')
                chunk=response.read(1024*1024)
                if not chunk:break
                total+=len(chunk)
                if total>asset['size'] or total>MAX_ARCHIVE:raise ValueError('Oversized update')
                sha.update(chunk);out.write(chunk);progress(5+int(total/asset['size']*75),'download')
        if total!=asset['size'] or 'sha256:'+sha.hexdigest()!=asset['digest']:raise ValueError('Update integrity check failed')
    except Exception:
        path.unlink(missing_ok=True);raise
    return path

def stage(archive,install_root,expected_version,progress=lambda *args:None):
    """Accept an exact hashed file inventory, no links, no paths outside Application."""
    root=Path(install_root).resolve();target=root/'Application'
    if not target.is_dir() or target.is_symlink() or not (target/'PhDexLab.exe').is_file():raise ValueError('Not a portable PhDexLab installation')
    stage_root=root/('.PhDexLab-update-'+uuid.uuid4().hex)
    try:
        with zipfile.ZipFile(archive) as z:
            entries=z.infolist();names=[i.filename for i in entries]
            if len(names)!=len(set(n.casefold() for n in names)) or len(entries)>20000:raise ValueError('Duplicate or excessive archive entries')
            if sum(i.file_size for i in entries)>MAX_EXPANDED:raise ValueError('Expanded update too large')
            for info in entries:
                parts=PurePosixPath(info.filename).parts
                raw_parts=info.filename.rstrip('/').split('/')
                if any(p in ('','.') for p in raw_parts) or any(ord(c)<32 for c in info.filename):raise ValueError('Non-canonical archive path')
                if not parts or '\\' in info.filename or ':' in info.filename or info.filename.startswith('/') or any(p in ('.','..') or p.endswith((' ','.')) for p in parts):raise ValueError('Unsafe archive path')
                if any(re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',p) for p in parts):raise ValueError('Reserved archive filename')
                if (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Archive symlinks are forbidden')
                if parts[0]!='Application' and info.filename!='release.json':raise ValueError('Update may replace Application only')
            info=z.getinfo('release.json')
            if info.file_size>2*1024*1024:raise ValueError('Manifest too large')
            manifest=json.loads(z.read('release.json'))
            if manifest.get('schema')!=1 or manifest.get('repository')!=REPOSITORY or manifest.get('version')!=expected_version:raise ValueError('Wrong update manifest')
            files=manifest['files'];actual={i.filename for i in entries if not i.is_dir() and i.filename!='release.json'}
            if not isinstance(files,dict) or set(files)!=actual or 'Application/PhDexLab.exe' not in files:raise ValueError('Update inventory mismatch')
            stage_root.mkdir()
            for index,name in enumerate(sorted(actual)):
                sha=hashlib.sha256();dest=stage_root.joinpath(*PurePosixPath(name).parts);dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(name) as src,dest.open('wb') as out:
                    while chunk:=src.read(1024*1024):sha.update(chunk);out.write(chunk)
                if sha.hexdigest()!=files[name]:raise ValueError('File integrity check failed: '+name)
                progress(80+int((index+1)/len(actual)*19),'verify')
            if (stage_root/'Application'/'PhDexLab.exe').read_bytes()[:2]!=b'MZ':raise ValueError('Invalid Windows executable')
        return stage_root
    except Exception:
        if stage_root.exists():shutil.rmtree(stage_root)
        raise

def schedule_install(stage_root,install_root,parent_pid=None,relaunch=True):
    root=Path(install_root).resolve();staged=Path(stage_root).resolve()
    if staged.parent!=root or not re.fullmatch(r'\.PhDexLab-update-[0-9a-f]{32}',staged.name):raise ValueError('Invalid update stage')
    if not (staged/'Application'/'PhDexLab.exe').is_file():raise ValueError('Update stage is missing')
    updates=user_data_dir()/'updates';updates.mkdir(parents=True,exist_ok=True)
    nonce=uuid.uuid4().hex;script=updates/('install-'+nonce+'.ps1');job=updates/('job-'+nonce+'.json')
    script.write_text((Path(__file__).parent/'assets'/'install-update.ps1').read_text(encoding='utf-8'),encoding='utf-8-sig')
    job.write_text(json.dumps(dict(root=str(root),stage=str(staged),pid=parent_pid or os.getpid(),relaunch=bool(relaunch),receipt=str(updates/'last-install.json'))),encoding='utf-8')
    executable=Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    return subprocess.Popen([str(executable),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(script),'-Job',str(job)],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),close_fds=True)
