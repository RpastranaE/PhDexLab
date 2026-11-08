import os,time,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from phdexlab.interface import Window
from phdexlab.data_entry import demo_varieties,normalize
from phdexlab.protocols import FE,catalog
from phdexlab.integration import create_experiment,dump
from phdexlab.paths import Layout
from phdexlab.origin import remove_empty_default_book

def app():return QApplication.instance() or QApplication([])

def test_demo_varieties_share_only_one_calibration():
    a=app();w=Window();w.load_demo(True);rows=normalize(w.raw.records(),FE)
    assert len(rows)==48
    assert {r['sample_id'] for r in rows if r['kind']=='sample'}=={'Variety A','Variety B','Variety C'}
    assert len([r for r in rows if r['kind']=='standard'])==15
    assert len(w.demo_menu.actions())==2
    assert w.tabs.count()==2 and not hasattr(w,'field_help')
    assert not w.log_toggle.text() and not w.help_button.text()
    w.show_help();assert w.help_dialog.isVisible();w.close()

def test_manual_protocol_catalog_roundtrip(tmp_path):
    a=app();w=Window();w.variant_folder=tmp_path/'variants'
    w.prepare_protocol('FRAP manual',0)
    assert w.tabs.currentWidget()==w.parameters and w.dirty
    for r in range(w.parameters.rowCount()):
        if w.parameters.item(r,0).data(256)=='time_min':w.parameters.item(r,1).setText('8')
    with patch('phdexlab.interface.QInputDialog.getText',return_value=('FRAP manual',True)):w.save_variant()
    saved=catalog(w.variant_folder)[-1]
    assert saved['time_min']==8 and saved['version']==1 and saved['id'].startswith('frap-custom-')
    original=list(w.variant_folder.glob('*.json'))[0].read_bytes()
    with patch('phdexlab.interface.QInputDialog.getText',return_value=('FRAP manual 2',True)):w.save_variant()
    assert len(list(w.variant_folder.glob('*.json')))==2
    assert original in [p.read_bytes() for p in w.variant_folder.glob('*.json')]
    w.close()

def test_phase_progress_and_direct_open(tmp_path):
    a=app();w=Window();root=create_experiment(tmp_path/'EXP-v4',demo_varieties());w.load_folder(root);w.started=time.monotonic()
    fills=[]
    for step in range(1,7):
        dump(Layout(root).meta/'progress.json',dict(step=step,total=6,label='Etapa de prueba',busy=True));w.poll_progress();fills.append(w.progress.value())
        assert w.progress.maximum()==100 and 'Etapa de prueba' in w.progress.format() and w.progress.isTextVisible()
    assert fills==sorted(set(fills)) and fills[-1]<100
    dump(Layout(root).meta/'progress.json',dict(step=6,total=6,label='Finalizada',busy=False,state='complete'));w.poll_progress();assert w.progress.value()==100
    Layout(root).project.write_bytes(b'test-opju-placeholder')
    with patch('phdexlab.interface.os.startfile') as start:
        w.open_excel();w.open_origin();assert [c.args[0] for c in start.call_args_list]==[Layout(root).master,Layout(root).project]
    w.close()

def test_empty_default_book_cleanup_preserves_user_data():
    class Sheet:
        def __init__(self,rows=0,label=''):self.rows=rows;self.name='Sheet1';self.label=label
        def get_labels(self,type):return [self.label] if type=='L' else []
    class Book:
        name='Book1'
        def __init__(self,ws):self.ws=ws;self.removed=False
        def __iter__(self):return iter([self.ws])
        def destroy(self):self.removed=True
    class OP:
        def __init__(self,b):self.b=b
        def pages(self,type):return [self.b]
    for rows,label,expected in ((0,'',True),(1,'',False),(0,'My labels',False)):
        book=Book(Sheet(rows,label));remove_empty_default_book(OP(book));assert book.removed==expected


def test_status_replace_retries_transient_windows_reader(tmp_path):
    from phdexlab.integration import dump
    path=tmp_path/'status.json';dump(path,{'stage':1})
    import os
    replace=os.replace
    attempts=[]
    def temporarily_locked(src,dst):
        attempts.append(1)
        if len(attempts)<3:raise PermissionError('Reader temporarily denies replacement')
        return replace(src,dst)
    with patch('phdexlab.integration.os.replace',side_effect=temporarily_locked):dump(path,{'stage':2})
    assert json.loads(path.read_text(encoding='utf-8'))=={'stage':2} and len(attempts)==3

def test_progress_file_error_does_not_abort_worker(tmp_path,capsys):
    from phdexlab import worker
    seen=[]
    def calculation(folder,mode,progress):
        progress(2,'Excel');seen.append('calculated');return {'state':'complete'}
    with patch('phdexlab.worker.dump',side_effect=PermissionError('status file unavailable')),patch('phdexlab.worker.refresh',side_effect=calculation):worker.run([str(tmp_path),'connector'])
    assert seen==['calculated'] and 'Progress update skipped' in capsys.readouterr().err
