import copy,hashlib,io,json,os,zipfile
from pathlib import Path
from unittest.mock import patch
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from phdexlab import updater
from phdexlab.graph_styles import selection,resolved,save_presentation,read_presentation,presentation_hash,save_user_style,user_styles
from phdexlab.integration import dump
from phdexlab.paths import Layout
from PySide6.QtWidgets import QApplication

@pytest.fixture(autouse=True)
def isolate(monkeypatch,tmp_path):monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'personal'))

def test_custom_roles_roundtrip_and_cache_revision(tmp_path):
    folder=tmp_path/'EXP';Layout(folder).prepare();old=presentation_hash(folder);s=selection('teal')
    s['settings']['results'].update(marker='D',per_sample=True)
    s['settings']['calibration'].update(colors=['#123456','#654321'],marker='^',line=':',width=2.2)
    save_presentation(folder,s);loaded=resolved(read_presentation(folder))
    assert loaded['results']['marker']=='D' and loaded['calibration']['marker']=='^'
    assert loaded['calibration']['colors']==['#123456','#654321'] and presentation_hash(folder)!=old
    revision=read_presentation(folder)['revision'];save_presentation(folder,s);assert read_presentation(folder)['revision']==revision
    s['settings']['calibration']['colors'][0]='#ABCDEF';save_presentation(folder,s);assert read_presentation(folder)['revision']==revision+1

def test_schema_one_preserves_appearance(tmp_path):
    Layout(tmp_path).prepare();dump(Layout(tmp_path).meta/'presentation.json',dict(schema=1,style='violet',revision=3))
    s=resolved(read_presentation(tmp_path));assert s['calibration']['marker']=='D' and s['results']['fill']=='#E5DDF0'
    assert read_presentation(tmp_path)['schema']==1

@pytest.mark.parametrize('role,field,value',[('calibration','colors',['red','blue']),('results','size',0),('dose','line','code;'),('typography','font','Arial);exit;'),('typography','tick_size',6),('results','per_sample','yes')])
def test_styles_reject_invalid_fields(role,field,value):
    s=selection();s['settings'][role][field]=value
    with pytest.raises(ValueError):selection(s)

def test_personal_styles_exclude_experiment_data():
    data=selection('earth');save_user_style('My journal style',data);assert user_styles()[0]['settings']==data['settings']
    assert set(user_styles()[0])=={'schema','name','style','settings'}

def test_editor_role_independence_and_live_preview(tmp_path):
    q=QApplication.instance() or QApplication([])
    from phdexlab.graph_dialog import GraphDialog
    d=GraphDialog('classic');before=copy.deepcopy(d.selected['settings']['calibration'])
    d.controls['results','marker'].setCurrentIndex(4);d.controls['results','per_sample'].setChecked(True)
    d.set_palette('results',['#123456','#ABCDEF']);assert d.selected['settings']['calibration']==before
    assert d.selected['settings']['results']['marker']=='D' and not d.result_preview.pixmap().isNull()
    d.show();q.processEvents();d.grab().save(str(tmp_path/'style-editor.png'));d.reject()

def test_semantic_versions_and_settings():
    assert updater.version('v0.10.0')>updater.version('0.9.9')
    for bad in ('v1.2','1.2.3-beta','https://malicious','1.2.3;exit'):
        with pytest.raises(ValueError):updater.version(bad)
    assert updater.settings()['automatic'];updater.set_automatic(False);assert not updater.settings()['automatic']

class Response(io.BytesIO):
    def __init__(self,data,url):super().__init__(data);self.url=url
    def geturl(self):return self.url

def release_data():
    return dict(tag_name='v9.0.0',html_url=updater.REPO_URL+'/releases/tag/v9.0.0',draft=False,prerelease=False,assets=[dict(name=updater.ASSET_NAME,size=3,digest='sha256:'+hashlib.sha256(b'zip').hexdigest(),browser_download_url=updater.REPO_URL+'/releases/download/v9.0.0/'+updater.ASSET_NAME)])

def test_latest_accepts_only_expected_stable_release():
    data=release_data();opened=[]
    def opener(req,timeout):opened.append(req);return Response(json.dumps(data).encode(),updater.API_URL)
    assert updater.latest(opener)['newer'];assert opened[0].get_full_url()==updater.API_URL
    for change in ({'prerelease':True},{'html_url':'https://evil.example/release'}):
        data.update(change)
        with pytest.raises(ValueError):updater.latest(opener)
        data=release_data()
    data['assets'][0]['digest']=None
    with pytest.raises((ValueError,TypeError)):updater.latest(opener)

def test_download_verifies_digest_and_removes_partial(tmp_path):
    r=dict(asset=release_data()['assets'][0]);dest=tmp_path/'update.zip'
    assert updater.download(r,dest,opener=lambda req,timeout:Response(b'zip','https://release-assets.githubusercontent.com/file'))==dest
    with pytest.raises(ValueError):updater.download(r,dest,opener=lambda req,timeout:Response(b'bad','https://release-assets.githubusercontent.com/file'))
    assert not dest.exists()
    with pytest.raises(ValueError):updater.download(r,dest,opener=lambda req,timeout:Response(b'zip','https://evil.example/file'))

def archive(tmp_path,extra=None,wrong_hash=False):
    files={'Application/PhDexLab.exe':b'MZtest','Application/_internal/runtime.dll':b'runtime'}
    if extra:files.update(extra)
    manifest=dict(schema=1,repository=updater.REPOSITORY,version='9.0.0',files={name:hashlib.sha256(data).hexdigest() for name,data in files.items()})
    if wrong_hash:manifest['files']['Application/PhDexLab.exe']='0'*64
    path=tmp_path/'package.zip'
    with zipfile.ZipFile(path,'w') as z:
        for name,data in files.items():z.writestr(name,data)
        z.writestr('release.json',json.dumps(manifest))
    return path

def install_root(tmp_path):
    root=tmp_path/'install';app=root/'Application';app.mkdir(parents=True);(app/'PhDexLab.exe').write_bytes(b'MZold');(root/'EXP.xlsx').write_bytes(b'experiment');return root

def test_staging_does_not_overwrite_install_or_experiment(tmp_path):
    root=install_root(tmp_path);stage=updater.stage(archive(tmp_path),root,'9.0.0')
    assert (stage/'Application/PhDexLab.exe').read_bytes()==b'MZtest'
    assert (root/'Application/PhDexLab.exe').read_bytes()==b'MZold' and (root/'EXP.xlsx').read_bytes()==b'experiment'

@pytest.mark.parametrize('name',['../escape.exe','Application/../escape.exe','Application\\escape.exe','Application/C:bad.exe','Application/NUL','EXP/RAW.xlsx','Application/CON.txt','/Application/x'])
def test_unsafe_update_archives_are_rejected(tmp_path,name):
    root=install_root(tmp_path)
    with pytest.raises(ValueError):updater.stage(archive(tmp_path,{name:b'bad'}),root,'9.0.0')
    assert not list(root.glob('.PhDexLab-update-*'))

def test_file_hash_and_wrong_version_rejected(tmp_path):
    root=install_root(tmp_path)
    with pytest.raises(ValueError):updater.stage(archive(tmp_path,wrong_hash=True),root,'9.0.0')
    with pytest.raises(ValueError):updater.stage(archive(tmp_path),root,'8.0.0')
    assert not list(root.glob('.PhDexLab-update-*'))

def test_install_job_is_scoped_and_hidden(tmp_path):
    root=install_root(tmp_path);stage=updater.stage(archive(tmp_path),root,'9.0.0')
    with patch('phdexlab.updater.subprocess.Popen') as run:
        updater.schedule_install(stage,root,parent_pid=123,relaunch=False);args=run.call_args.args[0]
        assert '-NonInteractive' in args and '-File' in args
    with pytest.raises(ValueError):updater.schedule_install(tmp_path,root)

def test_close_preserves_unsaved_work_on_cancel():
    q=QApplication.instance() or QApplication([])
    from phdexlab.workspace import Window
    from PySide6.QtWidgets import QMessageBox
    w=Window();w.load_demo();w.show();q.processEvents();w.dirty=True
    with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel):assert not w.close()
    assert w.isVisible() and w.dirty;w.dirty=False;w.close()

def test_duplicate_case_paths_and_symlinks_rejected(tmp_path):
    root=install_root(tmp_path);path=archive(tmp_path,{'Application/PHDEXLAB.EXE':b'MZother'})
    with pytest.raises(ValueError):updater.stage(path,root,'9.0.0')
    path=archive(tmp_path)
    with zipfile.ZipFile(path,'a') as z:
        info=zipfile.ZipInfo('Application/link');info.external_attr=(0o120777<<16);z.writestr(info,'../../outside')
    with pytest.raises(ValueError):updater.stage(path,root,'9.0.0')

def test_update_worker_respects_disabled_downloads(tmp_path):
    q=QApplication.instance() or QApplication([])
    from phdexlab.updater_ui import UpdateWorker
    received=[];worker=UpdateWorker(tmp_path,False);worker.completed.connect(lambda result,error:received.append((result,error)))
    with patch('phdexlab.updater.latest',return_value=dict(newer=True,version='9.0.0')),patch('phdexlab.updater.download') as download:
        worker.run();assert not download.called and received[0][0]['stage'] is None and received[0][1]==''

def test_disabling_automatic_discards_only_staged_payload(tmp_path):
    q=QApplication.instance() or QApplication([])
    from phdexlab.workspace import Window
    w=Window();root=install_root(tmp_path);staged=updater.stage(archive(tmp_path),root,'9.0.0');w.updates.root=root;w.updates.ready=staged;updater.set_automatic(False)
    with patch('phdexlab.updater.schedule_install') as install:assert w.updates.prepare_close() and not install.called
    assert not staged.exists() and (root/'EXP.xlsx').read_bytes()==b'experiment';w.dirty=False;w.close()

def test_print_units_use_math_glyphs_for_windows_font_compatibility():
    from phdexlab.multi_publication import print_text
    assert print_text('µmol L⁻¹; g⁻¹')=='µmol L$^{-1}$; g$^{-1}$'
    assert print_text('Inhibition (%)')=='Inhibition (%)'
