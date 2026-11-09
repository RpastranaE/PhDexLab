"""Regression checks for installer-era usability and frozen update metadata."""
import copy,io,json,os
from unittest.mock import patch
from urllib.error import HTTPError
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QStyleOptionViewItem,QAbstractButton,QToolTip
from PySide6.QtCore import QEvent,QPoint
from PySide6.QtGui import QHelpEvent
from phdexlab import i18n,updater
from phdexlab.appearance import preferences
from phdexlab.method_catalog import ALL
from phdexlab.protocol_texts import display_value
from phdexlab.graph_styles import resolved,selection
from phdexlab.graph_dialog import preview

@pytest.fixture(autouse=True)
def isolated(monkeypatch,tmp_path):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'personal'))
    i18n.set_language('en')
    yield
    i18n.set_language('es')

def app():return QApplication.instance() or QApplication([])

def test_fresh_english_and_saved_spanish():
    from phdexlab.appearance import save_preferences
    assert preferences()['language']=='en'
    save_preferences('es','dark');assert preferences()==dict(language='es',theme='dark')

def test_builtin_names_sources_and_display_translations():
    for p in ALL:
        assert 'BORRADOR' not in p['name']+p['status']
        assert p['source'].startswith('https://doi.org/')
        for field in ('name','notes','reagents','mass_basis','qc_policy','standard_range'):
            assert display_value(field,p.get(field,''))==p.get(field,'')
    assert display_value('notes','My custom text')=='My custom text'
    i18n.set_language('es');assert display_value('mass_basis','dry leaf')=='hoja seca'

def test_language_changes_preserve_protocol_and_custom_text():
    q=app()
    from phdexlab.workspace import Window
    w=Window();assert 'Draft' in w.assay_list.item(0).text();canonical=w.protocol()
    w.language_selector.setCurrentIndex(0);assert w.protocol()==canonical
    w.language_selector.setCurrentIndex(1);assert w.protocol()==canonical
    w.set_protocol(dict(canonical,notes='Operator-authored text'));assert w.protocol()['notes']=='Operator-authored text'
    w.language_selector.setCurrentIndex(0);assert w.protocol()['notes']=='Operator-authored text'
    w.dirty=False;w.close()

def test_choose_type_removes_complete_reading():
    q=app()
    from phdexlab.workspace import Window
    w=Window();w.load_demo();n=len(w.raw.records());table=w.raw
    delegate=table.itemDelegateForColumn(1);index=table.model().index(0,1)
    editor=delegate.createEditor(table,QStyleOptionViewItem(),index);editor.setCurrentIndex(0)
    delegate.setModelData(editor,table.model(),index)
    assert len(table.records())==n-1 and all(table.item(0,c).text()=='' for c in range(table.columnCount()))
    w.dirty=False;w.close()

@pytest.mark.parametrize('role,field,value',[
 ('results','marker','D'),('results','open',True),('results','size',10),('results','fill','#FF0000'),('results','error','#FF0000'),('results','per_sample',True),
 ('calibration','colors',['#CC0000','#00CC00']),('calibration','marker','^'),('calibration','width',3),('calibration','line',':'),('calibration','error','#FF0000'),
 ('dose','colors',['#CC0000','#00CC00']),('dose','marker','s'),('dose','line','--'),('dose','width',3),('dose','open',True),('dose','error','#FF0000'),
 ('typography','font','Times New Roman'),('typography','label_size',14),('typography','tick_size',14)])
def test_preview_reflects_controls(role,field,value):
    q=app();s=selection('classic');render_role=role if role!='typography' else 'dose'
    before=preview(resolved(s),role=render_role).toImage();s['settings'][role][field]=value
    after=preview(resolved(s),role=render_role).toImage();assert before!=after

def test_only_one_save_variant_and_hover_descriptions():
    q=app()
    from phdexlab.workspace import Window
    w=Window();w.show();q.processEvents()
    visible=[b for b in w.findChildren(QAbstractButton) if b.isVisible() and b.property('iconName')]
    assert all(b.toolTip() and b.accessibleName() for b in visible)
    saves=[b for b in visible if 'versioned variant' in b.toolTip()];assert len(saves)==1
    b=w.save_variant_button
    q.sendEvent(b,QHelpEvent(QEvent.Type.ToolTip,QPoint(1,1),b.mapToGlobal(QPoint(1,1))))
    assert QToolTip.text()==b.toolTip();QToolTip.hideText();w.dirty=False;w.close()

class Response(io.BytesIO):
    def __init__(self,data,url):super().__init__(json.dumps(data).encode());self.url=url
    def geturl(self):return self.url

def test_update_falls_back_only_to_matching_public_release():
    data=dict(schema=1,repository=updater.REPOSITORY,tag_name='v9.0.0',html_url=updater.REPO_URL+'/releases/tag/v9.0.0',assets=[dict(name=updater.ASSET_NAME,size=123,digest='sha256:'+'a'*64,browser_download_url=updater.REPO_URL+'/releases/download/v9.0.0/'+updater.ASSET_NAME)])
    def opener(req,timeout):
        if req.full_url==updater.API_URL:raise HTTPError(req.full_url,403,'Quota',{},None)
        assert req.full_url==updater.PUBLIC_METADATA
        return Response(data,'https://release-assets.githubusercontent.com/file')
    assert updater.latest(opener)['version']=='9.0.0'
    data['assets'][0]['browser_download_url']=updater.REPO_URL+'/releases/download/v1.0.0/'+updater.ASSET_NAME
    with pytest.raises(RuntimeError):updater.latest(opener)
