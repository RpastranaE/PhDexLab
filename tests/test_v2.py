import json
import shutil
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from phdexlab.paths import Layout,migrate_legacy
from phdexlab.data_entry import demo_rows,COLUMNS
from phdexlab.integration import create_experiment,verify
from phdexlab.excel import read_inputs
from phdexlab.interface import Window,configure_font
from phdexlab.ui_fields import FIELDS,KIND_LABELS

def app():
    a=QApplication.instance() or QApplication([]);configure_font(a);return a

def test_layout_named_and_separate(tmp_path):
    root=create_experiment(tmp_path/'EXP-012',demo_rows());l=Layout(root)
    assert l.master==root/'Documents'/'EXP-012.xlsx'
    assert l.project==root/'Documents'/'EXP-012.opju'
    assert (l.meta/'experiment.json').exists()
    assert not list(root.glob('*.json'))
    assert l.origin_figures('svg')==root/'Figures'/'Origin'/'SVG'

def test_legacy_lossless_migration(tmp_path):
    root=create_experiment(tmp_path/'CAR-021',demo_rows());l=Layout(root)
    initial=(l.meta/'raw.initial.json').read_bytes()
    # Reconstruct the old layout in this disposable fixture.
    shutil.move(l.master,root/'master.xlsx')
    for p in list(l.meta.iterdir()):shutil.move(p,root/p.name)
    (root/'_internal').rmdir()
    manifest=json.loads((root/'experiment.json').read_text());manifest.pop('file_stem');manifest['schema']=1
    (root/'experiment.json').write_text(json.dumps(manifest))
    verify(root);new=migrate_legacy(root);verify(root)
    assert new.master.exists() and new.master.name=='CAR-021.xlsx'
    assert (new.meta/'raw.initial.json').read_bytes()==initial
    assert (new.meta/'migration_v1_backup.zip').exists()

def test_hidden_auto_id_and_stability():
    a=app();w=Window();w.load_demo();assert w.raw.isColumnHidden(0)
    rows=w.raw.records();assert len(rows)==27
    # Drop the internal ID from a single entered row; its regenerated ID stays stable.
    w.raw.item(0,0).setText('')
    generated=w.raw.records()[0]['record_id']
    assert generated and w.raw.records()[0]['record_id']==generated
    assert w.raw.horizontalHeaderItem(9).text().startswith('Factor de dilución')
    assert all(FIELDS[k][1] for k in COLUMNS)
    w.close()

def test_custom_role_roundtrip(tmp_path):
    a=app();w=Window();w.load_demo();w.raw.add_role('Control fortificado','control')
    row=24;item=w.raw.item(row,1);item.setText('Control fortificado');item.setData(Qt.ItemDataRole.UserRole,'control')
    records=w.raw.records();assert records[row]['kind']=='control';assert records[row]['kind_label']=='Control fortificado'
    root=create_experiment(tmp_path/'EXP-role',records)
    rows,p=read_inputs(Layout(root).master);w.raw.load(rows)
    assert w.raw.item(row,1).text()=='Control fortificado'
    assert w.raw.records()[row]['kind']=='control'
    with pytest.raises(ValueError):w.raw.add_role('Control fortificado','control')
    w.close()

def test_paste_human_type_and_internal_headers():
    a=app();w=Window();w.load_demo()
    records=w.raw.records();text='\t'.join(COLUMNS)+'\n'+'\t'.join(str(records[0][k]) for k in COLUMNS)
    w.raw.setCurrentCell(0,1);w.raw.paste(text)
    assert w.raw.records()[0]['kind']=='blank'
    w.close()
