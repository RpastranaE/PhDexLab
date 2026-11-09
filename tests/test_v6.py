import copy,json,os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from pathlib import Path
from unittest.mock import patch
from openpyxl import Workbook
from PySide6.QtWidgets import QApplication,QMessageBox
from phdexlab import i18n
from phdexlab.data_templates import make_template,save_template,catalog,instantiate
from phdexlab.demonstrations import multi_demo
from phdexlab.graph_styles import read_presentation,save_presentation,presentation_hash,STYLES
from phdexlab.export_cache import store,restore
from phdexlab.excel import values,value_session
from phdexlab.experiments import create,refresh
from phdexlab.integration import dump,file_hash
from phdexlab.paths import Layout
from phdexlab.workspace import Window

@pytest.fixture(autouse=True)
def isolated_preferences(monkeypatch,tmp_path):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'user'));i18n.set_language('es')
    yield
    i18n.set_language('es')

def app():return QApplication.instance() or QApplication([])

def test_data_template_preserves_design_not_observations():
    assay=multi_demo(True)[5];original=copy.deepcopy(assay['rows']);template=make_template('DPPH series',assay['protocol'],original)
    assert original==assay['rows'] and not template['contains_readings']
    assert all(not r['A_end'] and not r['plateau'] for r in template['rows'])
    assert [r['dose_mg_mL'] for r in template['rows']]==[r['dose_mg_mL'] for r in original]
    first=instantiate(template,assay['protocol']);second=instantiate(template,assay['protocol'])
    assert {r['record_id'] for r in first}.isdisjoint(r['record_id'] for r in second)

def test_opt_in_template_keeps_readings_and_rejects_wrong_method():
    a,b=multi_demo()[:2];template=make_template('With readings',a['protocol'],a['rows'],True)
    assert template['contains_readings'] and template['rows'][0]['A_end']==a['rows'][0]['A_end']
    with pytest.raises(ValueError,match='compatible'):instantiate(template,b['protocol'])
    incompatible=copy.deepcopy(a['protocol']);incompatible['concentration_unit']='mg/L'
    with pytest.raises(ValueError,match='concentración'):instantiate(template,incompatible)
    save_template(template);assert catalog()[0]['name']=='With readings'

def test_gravimetric_template_clears_all_weighings():
    a=multi_demo(True)[6];template=make_template('Weighings',a['protocol'],a['rows'])
    assert all(r['tare_g']==r['initial_g']==r['final_g']=='' for r in template['rows'])

def test_style_selection_is_experiment_scoped(tmp_path):
    folder=create(tmp_path/'EXP',multi_demo()[:1]);initial=presentation_hash(folder)
    save_presentation(folder,'violet');assert read_presentation(folder)['style']=='violet' and presentation_hash(folder)!=initial
    revision=read_presentation(folder)['revision'];save_presentation(folder,'violet');assert read_presentation(folder)['revision']==revision
    with pytest.raises(ValueError):save_presentation(folder,'not-a-style')

def test_export_cache_refuses_corrupt_bytes(tmp_path):
    folder=create(tmp_path/'EXP',multi_demo()[:1]);p=Layout(folder).figures/'test.svg';p.write_bytes(b'<svg/>');entries=store(folder,[str(p.relative_to(folder))]);p.unlink()
    assert restore(folder,entries) and p.read_bytes()==b'<svg/>'
    next((Layout(folder).meta/'export_cache').iterdir()).write_bytes(b'broken');p.unlink();assert not restore(folder,entries) and not p.exists()

def test_excel_values_loaded_once_and_invalidated_after_edit(tmp_path):
    path=tmp_path/'book.xlsx';book=Workbook();book.active.title='A';book.active.append([1]);book.create_sheet('B').append([2]);book.save(path)
    from phdexlab import excel
    original=excel.load_workbook
    @value_session
    def run():
        assert values(path,'A')==[(1,)] and values(path,'B')==[(2,)]
        book.active['A1']=3;book.save(path);assert values(path,'A')==[(3,)]
    with patch.object(excel,'load_workbook',wraps=original) as loading:run();assert loading.call_count==2
    assert excel._value_cache.get() is None

def test_fast_update_only_accepts_intact_outputs(tmp_path):
    folder=create(tmp_path/'EXP',multi_demo()[:1]);l=Layout(folder);output=l.figures/'test.svg';output.write_bytes(b'<svg/>')
    from phdexlab import __version__
    report=dict(state='complete',app_version=__version__,origin_mode='none',excel_sha256=file_hash(l.master),presentation_hash=presentation_hash(folder),outputs={str(output.relative_to(folder)):file_hash(output)})
    dump(l.meta/'status.json',report);assert refresh(folder,'none')['reused']
    output.write_bytes(b'corrupt')
    with patch('phdexlab.experiments.write_master',side_effect=RuntimeError('REBUILD')):
        with pytest.raises(RuntimeError,match='REBUILD'):refresh(folder,'none')

def test_figures_button_opens_root_for_multiple_and_assay_for_one(tmp_path):
    q=app();w=Window();w.load_multi_demo();w.folder=tmp_path
    with patch('phdexlab.workspace.os.startfile') as opened:w.open_location('origin');assert opened.call_args.args[0]==Layout(tmp_path).figures
    w.assays=w.assays[:1]
    with patch('phdexlab.workspace.os.startfile') as opened:w.open_location('origin');assert opened.call_args.args[0]==Layout(tmp_path).figures
    exported=Layout(tmp_path).figures/w.assays[0]['id'];exported.mkdir();(exported/'result.svg').write_text('<svg/>')
    with patch('phdexlab.workspace.os.startfile') as opened:w.open_location('origin');assert opened.call_args.args[0]==Layout(tmp_path).figures/w.assays[0]['id']
    w.dirty=False;w.close()

def test_language_and_theme_do_not_change_input_data():
    q=app();w=Window();w.load_multi_demo();before=w.raw.records();w.dirty=False
    w.language_selector.setCurrentIndex(1);w.toggle_theme()
    assert w.raw.records()==before and not w.dirty and w.theme_dark
    assert w.tabs.tabText(0)=='1   Experimental readings' and 'Sample' in w.raw.horizontalHeaderItem(2).text()
    assert w.help_dialog.topics.item(0).text()=='1 · Start in two minutes'
    w.language_selector.setCurrentIndex(0);assert w.tabs.tabText(0)=='1   Lecturas experimentales' and w.raw.records()==before
    w.close();second=Window();assert second.theme_dark;second.close()

def test_template_kind_delegate_uses_current_schema():
    q=app();w=Window();w.load_multi_demo(True);w.assay_list.setCurrentRow(5);w.language_selector.setCurrentIndex(1)
    from PySide6.QtWidgets import QStyleOptionViewItem
    table=w.raw;delegate=table.itemDelegateForColumn(1);index=table.model().index(0,1);editor=delegate.createEditor(table,QStyleOptionViewItem(),index)
    editor.setCurrentIndex(1);delegate.setModelData(editor,table.model(),index)
    assert table.item(0,1).data(256)=='blank' and table.columns.index('kind_label')==11
    w.dirty=False;w.close()

def test_all_style_previews_render_with_distinct_symbols():
    q=app();from phdexlab.graph_dialog import preview
    assert len({style['symbol'] for style in STYLES.values()})==5
    assert all(not preview(style).isNull() for style in STYLES.values())

def test_template_buttons_complete_save_and_load():
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLineEdit,QDialog
    q=app();w=Window();w.load_multi_demo();original=w.raw.records();errors=[]
    def save_dialog():
        try:
            dialog=q.activeModalWidget();assert isinstance(dialog,QDialog);dialog.findChild(QLineEdit).setText('Reusable FRAP design');dialog.accept()
        except Exception as error:errors.append(error);q.activeModalWidget().reject()
    QTimer.singleShot(0,save_dialog);w.save_data_template();assert not errors and len(catalog())==1
    QTimer.singleShot(0,lambda:q.activeModalWidget().accept());w.load_data_template()
    loaded=w.raw.records();assert len(loaded)==len(original) and w.dirty
    assert all(row['A_end']=='' and row['mass_g']=='' for row in loaded)
    assert [r['sample_id'] for r in loaded]==[r['sample_id'] for r in original]
    w.dirty=False;w.close()

def test_origin_cleanup_preserves_nonempty_and_custom_folders():
    from phdexlab.multi_origin import remove_empty_starter_folders
    from types import SimpleNamespace
    class Folder:
        def __init__(self,path,pages=(),children=()):self.path=path;self.pages=pages;self.children=children
        def GetPath(self):return self.path
        def PageBases(self):return self.pages
        def GetFolders(self):return self.children
    children=[Folder('/EXP/Folder01/'),Folder('/EXP/Folder1/',pages=['user data']),Folder('/EXP/My empty folder/'),Folder('/EXP/Folder001/',children=['child'])]
    commands=[];root=SimpleNamespace(path='/EXP/',obj=Folder('/EXP/',children=children))
    op=SimpleNamespace(pe=SimpleNamespace(root_folder=lambda:root,cd=lambda path:None),lt_exec=commands.append)
    assert remove_empty_starter_folders(op)==['/EXP/Folder01/'] and len(commands)==1

def test_fast_update_rejects_stale_connector_path(tmp_path):
    from phdexlab import __version__
    folder=create(tmp_path/'EXP',multi_demo()[:1]);l=Layout(folder);output=l.figures/'test.svg';output.write_bytes(b'<svg/>');l.project.write_bytes(b'project')
    report=dict(state='complete',app_version=__version__,origin_mode='connector',excel_sha256=file_hash(l.master),project_sha256=file_hash(l.project),presentation_hash=presentation_hash(folder),outputs={str(output.relative_to(folder)):file_hash(output)},origin=dict(master_path='C:/previous/location/EXP.xlsx'))
    dump(l.meta/'status.json',report)
    with patch('phdexlab.experiments.write_master',side_effect=RuntimeError('RECONNECT')):
        with pytest.raises(RuntimeError,match='RECONNECT'):refresh(folder,'connector')
