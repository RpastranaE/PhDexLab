import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt
from phdexlab.interface import Window
from phdexlab.data_table import required_fields
from phdexlab.protocols import FE
from phdexlab.data_entry import normalize,demo_rows
from phdexlab.integration import create_experiment,file_hash
from phdexlab.paths import Layout

def app():return QApplication.instance() or QApplication([])

def test_required_fields_follow_protocol_and_kind():
    common=required_fields('blank',FE)
    assert 'A_initial' in common and 'dilution' not in common
    assert {'dilution','extract_mL','mass_g'} <= required_fields('sample',FE)
    assert {'expected','concentration'} <= required_fields('control',FE)
    assert 'A_initial' not in required_fields('sample',dict(FE,response='endpoint'))

def test_add_sample_shared_calibration_and_close(tmp_path):
    a=app();w=Window();w.load_demo()
    original=w.raw.records();standards=[r for r in original if r['kind']=='standard']
    with patch('phdexlab.interface.QInputDialog.getText',return_value=('Variedad B',True)),patch('phdexlab.interface.QInputDialog.getInt',side_effect=[(2,True),(3,True)]):w.add_sample()
    rows=w.raw.records()
    assert len(rows)==33 and [r for r in rows if r['kind']=='standard']==standards
    new=[r for r in rows if r['sample_id']=='Variedad B']
    assert len(new)==6 and {r['bio_id'] for r in new}=={'B1','B2'}
    assert all(not r['A_end'] and not r['dilution'] for r in new)
    assert w.dirty and '2 muestras distintas' in w.metrics.text()
    root=create_experiment(tmp_path/'EXP-close',demo_rows());w.load_folder(root);before=file_hash(Layout(root).master)
    w.raw.item(0,6).setText('0.05')
    with patch('phdexlab.interface.QMessageBox.question',return_value=QMessageBox.StandardButton.Cancel):w.close_experiment()
    assert w.folder==root
    with patch('phdexlab.interface.QMessageBox.question',return_value=QMessageBox.StandardButton.Discard):w.close_experiment()
    assert w.folder is None and not w.raw.records() and file_hash(Layout(root).master)==before
    w.close()

def test_compact_ui_rows_and_log():
    a=app();w=Window();w.show();a.processEvents()
    assert w.windowTitle()=='PhDexLab' and not w.log.isVisible()
    assert all(b.toolTip() and not b.text() and not b.icon().isNull() for b in w.buttons)
    assert w.raw.height()>w.height()*0.60 and w.raw.verticalHeader().defaultSectionSize()>=48
    count=w.raw.rowCount();w.row_count.setValue(7);w.add_rows();assert w.raw.rowCount()==count+7
    w.log_toggle.setChecked(True);assert w.log.isVisible()
    w.close()
