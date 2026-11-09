import copy,json,os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QTableWidgetItem
from phdexlab.data_table import RawTable
from phdexlab.demonstrations import multi_demo,mean_demo
from phdexlab.input_validation import diagnose,missing_fields
from phdexlab.workspace import Window
from phdexlab.experiments import create,read
from phdexlab.paths import Layout
from phdexlab.integration import file_hash
from phdexlab.results_view import ResultsView,snapshot

ROLE=Qt.ItemDataRole.UserRole+5
def app():return QApplication.instance() or QApplication([])

def test_missing_flags_are_opt_in_and_zero_is_not_missing():
    q=app();a=multi_demo()[0];row=next(r for r in a['rows'] if r['kind']=='sample')
    row['mass_g']='';table=RawTable();table.set_protocol(a['protocol']);table.load([row])
    col=table.columns.index('mass_g');assert not table.item(0,col).data(ROLE)
    table.set_validation_visible(True);assert table.item(0,col).data(ROLE)
    assert table.item(0,col).background().color().name()=='#fde7e9'
    table.setItem(0,col,QTableWidgetItem('0.5'));assert not table.item(0,col).data(ROLE)
    assert not table.item(0,col).background().color().name()=='#fde7e9'
    assert not any(table.item(10,c) and table.item(10,c).data(ROLE) for c in range(table.columnCount()))
    row.update(mass_g=.5,A_end=0,A_initial=0);assert not missing_fields(row,a['protocol'])

def test_required_rules_follow_role_signal_and_mean_precision():
    a=mean_demo()[0];p=a['protocol'];sample=next(r for r in a['rows'] if r['kind']=='sample')
    sample.update(technical_n='',technical_sd='');assert not missing_fields(sample,p)
    sample['mass_g']='';assert 'mass_g' in missing_fields(sample,p)
    sample.update(kind='control',expected='',dilution='',extract_mL='',mass_g='')
    assert 'expected' in missing_fields(sample,p) and 'mass_g' not in missing_fields(sample,p)
    p=copy.deepcopy(p);p.update(reading_signal='endpoint',response='endpoint');sample['A_initial']=''
    assert 'A_initial' not in missing_fields(sample,p)
    dpph=multi_demo(True)[5];r=dpph['rows'][0];r.update(time_min=0,plateau=False)
    assert 'time_min' not in missing_fields(r,dpph['protocol']) and 'plateau' not in missing_fields(r,dpph['protocol'])

def test_validation_identifies_all_assays_rows_and_bad_numeric_values():
    assays=multi_demo()[:2]
    for a in assays:
        row=next(r for r in a['rows'] if r['kind']=='sample');row.update(mass_g='',extract_mL='bad')
    issues=diagnose(assays)
    assert len(issues)==4 and {i['assay_id'] for i in issues}=={'A01_FRAP','A02_ABTS'}
    assert all(i['row'] and i['record_id'] for i in issues)
    assert {i['field'] for i in issues}=={'mass_g','extract_mL'}

def test_failed_export_saves_current_inputs_then_marks_and_reports_without_worker(tmp_path):
    q=app();w=Window();root=create(tmp_path/'EXP-draft',multi_demo()[:2]);w.load_folder(root)
    row=next(i for i in range(w.raw.rowCount()) if w.raw.item(i,1) and w.raw.item(i,1).data(Qt.ItemDataRole.UserRole)=='sample')
    c=w.raw.columns.index('mass_g');w.raw.item(row,c).setText('');w.raw.item(row,w.raw.columns.index('notes')).setText('Saved before validation')
    assert w.dirty and not w.raw.item(row,c).data(ROLE)
    with patch('phdexlab.validation_dialog.ValidationDialog.exec',return_value=0),patch('phdexlab.interface.Window.start') as worker:
        w.update();assert not worker.called and w.proc is None
    stored=read(root)[0]['rows'][row];assert stored['mass_g'] is None and stored['notes']=='Saved before validation'
    assert w.raw.item(row,c).data(ROLE) and not w.dirty
    assert json.loads((Layout(root).meta/'status.json').read_text(encoding='utf-8'))['state']=='draft'
    issue=next(i for i in w.validation_dialog.issues if i['field']=='mass_g');w.locate_validation_issue(issue)
    assert w.raw.currentRow()==row and w.raw.currentColumn()==c
    w.raw.item(row,c).setText('0.5');assert not w.raw.item(row,c).data(ROLE)
    w.dirty=False;w.close()

def test_ready_update_saves_edited_values_and_runs_once(tmp_path):
    q=app();w=Window();root=create(tmp_path/'EXP-ready',multi_demo()[:1]);w.load_folder(root)
    c=w.raw.columns.index('A_end');w.raw.item(0,c).setText('0.034')
    with patch('phdexlab.interface.Window.start') as worker:
        w.update();assert worker.call_count==1
    assert read(root)[0]['rows'][0]['A_end']==.034 and not w.dirty
    w.close()


def test_update_commits_the_active_cell_editor_before_saving(tmp_path):
    from PySide6.QtWidgets import QLineEdit
    from PySide6.QtTest import QTest
    q=app();w=Window();root=create(tmp_path/'EXP-editor',multi_demo()[:1]);w.load_folder(root)
    w.show();q.processEvents();c=w.raw.columns.index('A_end');w.raw.setCurrentCell(0,c)
    w.raw.editItem(w.raw.item(0,c));q.processEvents()
    editor=q.focusWidget();assert isinstance(editor,QLineEdit)
    editor.selectAll();QTest.keyClicks(editor,'0.045')
    with patch('phdexlab.interface.Window.start') as worker:
        w.update();assert worker.call_count==1
    assert read(root)[0]['rows'][0]['A_end']==.045 and not w.dirty
    w.close()

def test_autosave_never_overwrites_external_changes(tmp_path):
    q=app();w=Window();root=create(tmp_path/'EXP-conflict',multi_demo()[:1]);w.load_folder(root)
    w.raw.item(0,w.raw.columns.index('A_end')).setText('0.034')
    from phdexlab.experiments import save
    external=read(root);external[0]['rows'][0]['notes']='External change';save(root,external,file_hash(Layout(root).master))
    before=Layout(root).master.read_bytes()
    with pytest.raises(RuntimeError,match='cambió'):w.update()
    assert Layout(root).master.read_bytes()==before
    w.dirty=False;w.close()


def test_new_experiment_update_saves_once_without_extra_question(tmp_path):
    q=app();w=Window();w.load_multi_demo(False)
    with patch('phdexlab.workspace.QFileDialog.getExistingDirectory',return_value=str(tmp_path)),patch('phdexlab.workspace.QInputDialog.getText',return_value=('EXP-new',True)),patch('phdexlab.workspace.QMessageBox.exec') as question,patch('phdexlab.interface.Window.start') as worker:
        w.update();assert worker.call_count==1 and not question.called
    assert w.folder==tmp_path/'EXP-new' and len(read(w.folder))==5
    w.close()


def test_unsaved_update_cancel_preserves_the_table():
    q=app();w=Window();w.load_multi_demo(False);before=w.raw.records()
    with patch('phdexlab.workspace.QFileDialog.getExistingDirectory',return_value=''),patch('phdexlab.interface.Window.start') as worker:
        w.update();assert not worker.called
    assert w.folder is None and w.raw.records()==before
    w.dirty=False;w.close()


def test_partial_calculation_requires_explicit_dialog_choice(tmp_path):
    q=app();w=Window();assays=multi_demo()[:2];next(r for r in assays[0]['rows'] if r['kind']=='sample')['mass_g']=''
    w.load_folder(create(tmp_path/'EXP-partial',assays))
    def choose(dialog):dialog.continue_partial();return 1
    with patch('phdexlab.validation_dialog.ValidationDialog.exec',choose),patch('phdexlab.interface.Window.start') as worker:
        w.update();assert worker.call_count==1
    assert w._validation_requested
    w.dirty=False;w.close()

def test_result_cards_preserve_excel_values_and_hide_stale_data(tmp_path):
    q=app();a=multi_demo()[0];root=create(tmp_path/'EXP-results',[a]);l=Layout(root)
    l.meta.joinpath('status.json').write_text(json.dumps(dict(state='complete',presentation_hash=__import__('phdexlab.graph_styles',fromlist=['presentation_hash']).presentation_hash(root))),encoding='utf-8')
    value=1.234567891234567
    data=dict(state='ready',summary=[['Variety A',3,value,.1]],results=[['sample','Variety A','B1',3,value,.01,1,'OK',a['protocol']['result_unit']]],calibration=dict(slope=.001,intercept=.01,r2=.999),figures=[],figure_state='missing')
    view=ResultsView()
    with patch('phdexlab.results_view.snapshot',return_value=data) as reader:
        view.set_context(root,a);assert view.cards[0].text()==str(value) and view.cards[0].isReadOnly()
        view.set_context(root,a);assert reader.call_count==1
        old_frames=list(view.card_frames)
        view.set_context(root,a,dirty=True);assert not view.cards and view.data is None
        assert all(frame.parentWidget().isHidden() for frame in old_frames)
        view.set_context(root,a,busy=True);assert not view.cards
        reader.return_value=dict(state='stale_excel');view.set_context(root,a);assert not view.cards
    view.close()

def test_snapshot_blocks_changed_excel_before_reading_values(tmp_path):
    a=multi_demo()[0];root=create(tmp_path/'EXP-hash',[a]);l=Layout(root)
    l.meta.joinpath('status.json').write_text(json.dumps(dict(excel_sha256='outdated')),encoding='utf-8')
    with patch('phdexlab.results_view.load_workbook') as reader:
        assert snapshot(root,a)['state']=='stale_excel';assert not reader.called


def test_snapshot_uses_only_verified_origin_exports_for_selected_assay(tmp_path):
    from types import SimpleNamespace
    a=multi_demo()[0];root=create(tmp_path/'EXP-figures',[a]);l=Layout(root);l.project.write_bytes(b'project fixture')
    path=l.figures/a['id']/'Origin/PNG/EXP-figures_A01_FRAP_results.png';path.parent.mkdir(parents=True);path.write_bytes(b'image fixture')
    name=str(path.relative_to(l.root));report=dict(state='complete',excel_sha256=file_hash(l.master),project_sha256=file_hash(l.project),assays={a['id']:dict(state='calculated')},outputs={name:file_hash(path)},origin=dict(project_saved=True,master_path=str(l.master),exports=[name],errors=[]))
    def store():l.meta.joinpath('status.json').write_text(json.dumps(report),encoding='utf-8')
    class Book:
        def __getitem__(self,name):
            rows=[['header']]
            if name.endswith('Calibration'):rows=[[None]*10 for _ in range(5)];rows[2][9]=.001;rows[3][9]=.01;rows[4][9]=.999
            return SimpleNamespace(values=iter(rows))
        def close(self):pass
    store()
    with patch('phdexlab.results_view.load_workbook',side_effect=lambda *args,**kwargs:Book()):
        result=snapshot(root,a);assert result['figure_state']=='ready' and result['figures'][0][1]==path.resolve()
        path.write_bytes(b'changed image');assert snapshot(root,a)['figure_state']=='stale'
        report['origin']['project_saved']=False;store();assert snapshot(root,a)['figure_state']=='missing'
