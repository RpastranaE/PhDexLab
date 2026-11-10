import copy,json
from unittest.mock import patch
import pytest
from PySide6.QtWidgets import QMessageBox,QApplication,QTextBrowser
from phdexlab import libraries,i18n
from phdexlab.library_dialog import LibraryDialog
from phdexlab.workspace import Window
from phdexlab.data_templates import make_template,save_template,catalog
from phdexlab.protocols import save_variant
from phdexlab.demonstrations import multi_demo
from phdexlab.experiments import create,read
from phdexlab.paths import Layout
from phdexlab.integration import file_hash

@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'user'));i18n.set_language('en')
    yield
    i18n.set_language('es')

def test_delete_data_template_leaves_loaded_rows_and_experiment_intact(tmp_path):
    a=multi_demo()[0];template=make_template('Reusable FRAP',a['protocol'],a['rows']);path=save_template(template)
    root=create(tmp_path/'EXP',[a]);before=file_hash(Layout(root).master);rows=copy.deepcopy(a['rows'])
    libraries.remove('data',libraries.entries('data')[0])
    assert not path.exists() and not catalog() and rows==a['rows']
    assert before==file_hash(Layout(root).master) and read(root)[0]['protocol']==a['protocol']

def test_deleting_custom_variant_does_not_change_assay_snapshot(tmp_path):
    w=Window();w.load_multi_demo();p=w.protocol();p.update(name='My FRAP',version=42)
    path=save_variant(w.variant_folder,p);w.set_protocol(p);w.mark_dirty();w.commit_active();before=copy.deepcopy(w.assays)
    entry=next(e for e in libraries.entries('protocol') if not e['included']);libraries.remove('protocol',entry)
    w.variants=libraries.variants();w.populate_variants(w.protocol())
    assert not path.exists() and w.assays==before and w.protocol()==p and w.dirty
    assert w.variant.currentData() is None and 'in this assay' in w.variant.currentText()
    w.dirty=False;w.close()

def test_included_variants_hide_persist_and_restore_without_changing_all():
    from phdexlab.method_catalog import ALL
    before=copy.deepcopy(ALL);entry=libraries.entries('protocol')[0]
    libraries.remove('protocol',entry)
    assert entry['key'] not in {e['key'] for e in libraries.entries('protocol')}
    assert next(e for e in libraries.entries('protocol',include_hidden=True) if e['key']==entry['key'])['hidden']
    w=Window();assert entry['payload'] not in w.variants;w.close()
    libraries.restore(entry);assert entry['payload'] in libraries.variants() and ALL==before

def test_stale_file_cannot_be_deleted():
    a=multi_demo()[0];p=save_template(make_template('A',a['protocol'],a['rows']));entry=libraries.entries('data')[0]
    original=p.read_text(encoding='utf-8');p.write_text(original+' ',encoding='utf-8')
    with pytest.raises(ValueError,match='ha cambiado'):libraries.remove('data',entry)
    assert p.exists()

def test_manager_cancel_delete_search_and_restore():
    a=multi_demo()[0];path=save_template(make_template('Find me',a['protocol'],a['rows']))
    dialog=LibraryDialog('data');assert dialog.table.rowCount()==1
    dialog.search.setText('nothing');assert not dialog.delete.isEnabled()
    dialog.search.setText('find');assert dialog.delete.isEnabled()
    with patch('phdexlab.library_dialog.QMessageBox.exec',return_value=QMessageBox.StandardButton.No):dialog.remove_selected()
    assert path.exists() and not dialog.changed
    with patch('phdexlab.library_dialog.QMessageBox.exec',return_value=QMessageBox.StandardButton.Yes):dialog.remove_selected()
    assert not path.exists() and dialog.changed and dialog.table.rowCount()==0
    protocol=LibraryDialog('protocol');key=protocol.selected()['key']
    with patch('phdexlab.library_dialog.QMessageBox.exec',return_value=QMessageBox.StandardButton.Yes):protocol.remove_selected()
    row=next(i for i,e in enumerate(protocol.visible) if e['key']==key);protocol.table.selectRow(row)
    assert protocol.restore.isEnabled() and not protocol.delete.isEnabled();protocol.restore_selected()
    assert key in {e['key'] for e in libraries.entries('protocol')}

def test_library_available_without_assay_and_management_keeps_edits():
    w=Window();assert w.templates_button.isEnabled() and not w.save_template_action.isEnabled()
    assert any(action.text()=='Manage protocol variants' for action in w.templates_menu.actions())
    w.load_multi_demo();before=w.raw.records();dirty=w.dirty;p=w.protocol()
    def manage(dialog):libraries.remove('protocol',dialog.items[0]);dialog.changed=True;return 0
    with patch('phdexlab.library_dialog.LibraryDialog.exec',manage):w.manage_library('protocol')
    assert w.raw.records()==before and w.protocol()==p and w.dirty==dirty
    w.dirty=False;w.close()

def test_zero_standard_and_blank_have_distinct_formula_roles():
    from phdexlab.calculations import plan
    a=multi_demo()[0];rows=a['rows'];formula=plan(rows,a['protocol'])
    assert '"blank"' in formula['Calibration']['J2']
    assert 'Calibration!$J$2' in formula['Processing']['C2']
    # The regression averages only standards: reagent blanks are not a second level.
    expected=len({(r['kind'],r['sample_id'],r['bio_id']) for r in rows if r['kind']=='standard'})
    assert len([key for key in formula['Calibration'] if key.startswith('A')])==expected

def test_results_folder_button_and_generic_unit_names(tmp_path):
    w=Window();w.load_multi_demo();w.folder=tmp_path;w.tabs.setCurrentWidget(w.results_view)
    assert w.results_view.figures_button.isEnabled()
    with patch('phdexlab.workspace.os.startfile') as opened:
        w.results_view.figures_button.click();assert opened.call_args.args[0]==Layout(tmp_path).figures
    label=w.raw.horizontalHeaderItem(w.raw.columns.index('bio_id')).text()
    assert 'Experimental unit' in label and 'Biological' not in label
    w.language_selector.setCurrentIndex(0)
    label=w.raw.horizontalHeaderItem(w.raw.columns.index('bio_id')).text();assert 'Unidad experimental' in label
    w.dirty=False;w.close()

def test_protocol_source_is_optional_in_validation_ui_and_saved_workbook(tmp_path):
    from phdexlab.assay_engine import ready_protocol,state
    a=multi_demo()[0];a['protocol']['source']='';ready_protocol(a['protocol']);assert state(a)[0]=='ready'
    root=create(tmp_path/'No-reference',[a]);assert not read(root)[0]['protocol']['source']
    w=Window();w.load_folder(root)
    row=next(i for i in range(w.parameters.rowCount()) if w.parameters.item(i,0).data(256)=='source')
    assert '*' not in w.parameters.cellWidget(row,0).text()
    w.close()

@pytest.mark.parametrize('mean,sd,expected',[
    (16,.8,('16.00','0.80')),(45.19656089320841,2.385833951392485,('45.2','2.4')),
    (123.456,.01234,('123.456','0.012')),(123.45,9.96,('123','10')),
    (1.234567,0,('1.235','0')),(1.234567,None,('1.235',None)),
    (-.00012345,.000001234,('-0.0001235','1.2e-6')),
    (12345,1234,('1.23e+4','1.2e+3')),
])
def test_reporting_rounds_display_without_changing_saved_numbers(mean,sd,expected):
    from phdexlab.reporting import rounded_pair
    original=(mean,sd);assert rounded_pair(mean,sd)==expected;assert (mean,sd)==original

def test_export_repair_removes_only_expected_title_overlines():
    import xml.etree.ElementTree as ET
    from phdexlab.origin_export import cleaned_svg
    raw=b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200">
    <g><path id="fit" d="M 10,10 L 100,100"/>
    <text x="50" y="180" font-size="20">Sample</text><path id="annotation-bar" d="M 50,163 L 120,163"/></g>
    <text x="50" y="180" font-size="20">Sample</text><path id="bad" d="M 50,163 L 120,163"/>
    <text x="0" y="0" font-size="20" transform="matrix(0 -1 1 0 30 150)">Result</text><path id="bad-y" d="M 13,150 L 13,90"/>
    <text x="150" y="100" font-size="20">Annotation</text><path id="wanted-bar" d="M 150,83 L 220,83"/>
    <text x="100" y="150" font-size="20">Sample</text><path id="not-overline" d="M 100,150 L 140,120"/>
    </svg>'''
    clean,count=cleaned_svg(raw,['Sample','Result']);assert count==2
    ids={e.get('id') for e in ET.fromstring(clean).iter()}
    assert {'fit','annotation-bar','wanted-bar','not-overline'}<=ids and not {'bad','bad-y'}&ids
    assert cleaned_svg(clean,['Sample','Result'])==(clean,0)

def test_entry_summary_counters_readiness_language_and_theme():
    w=Window();w.load_multi_demo();w.show();QApplication.processEvents()
    assert w.metrics.status.property('ready') is True
    assert w.metrics.status.text()=='Ready to calculate'
    assert w.metrics.values['samples'].text()=='3'
    assert w.metrics.captions['samples'].text()=='Samples' and w.metrics.height()==40
    assert '|' not in w.metrics.status.text() and 'Â·' not in w.metrics.assay.text()
    row=next(i for i,r in enumerate(w.raw.records()) if r['kind']=='sample')
    w.raw.item(row,w.raw.columns.index('mass_g')).setText('')
    from PySide6.QtTest import QTest
    QTest.qWait(400)
    assert w.metrics.status.property('ready') is False
    assert w.metrics.status.toolTip() and w.metrics.status.text()=='Review inputs'
    w.language_selector.setCurrentIndex(0);QApplication.processEvents()
    assert w.metrics.captions['sample'].text()=='Lecturas de muestras'
    assert w.metrics.status.text()=='Revisar entradas'
    w.toggle_theme();assert '#1D5540' in w.metrics.styleSheet()
    w.dirty=False;w.close()

def test_release_notes_first_install_upgrade_repeat_downgrade_and_legacy():
    from phdexlab.release_notes import show_on_launch,show_after_update
    from phdexlab.data_templates import user_data_dir
    from phdexlab import __version__
    from phdexlab.integration import dump
    w=Window();show_on_launch(w);assert w.help_dialog.isVisible()
    assert not hasattr(w,'whats_new_dialog');w.help_dialog.close()
    assert not show_after_update(w)
    path=user_data_dir()/'onboarding.json';dump(path,dict(help_seen=True,last_version='0.10.0',retained='yes'))
    assert show_after_update(w);assert w.whats_new_dialog.isVisible()
    assert 'standard deviation' in w.whats_new_dialog.findChild(QTextBrowser).toPlainText()
    w.whats_new_dialog.close();assert not show_after_update(w)
    assert json.loads(path.read_text())==dict(help_seen=True,last_version=__version__,retained='yes')
    dump(path,dict(help_seen=True,last_version='9.0.0'));assert not show_after_update(w)
    assert json.loads(path.read_text())['last_version']=='9.0.0'
    dump(path,dict(help_seen=True));i18n.set_language('es');assert show_after_update(w)
    assert w.whats_new_dialog.windowTitle()=='Novedades de PhDexLab';w.whats_new_dialog.close()
    assert not show_after_update(w);w.close()
