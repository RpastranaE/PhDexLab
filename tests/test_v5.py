import copy,json,os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from openpyxl import load_workbook
from PySide6.QtWidgets import QApplication,QMessageBox
from unittest.mock import patch
from phdexlab.method_catalog import ALL,TFC,ABTS,CUPRAC,MOISTURE_ADAPT,ASH_ADAPT
from phdexlab.assay_engine import state,clean,columns
from phdexlab.demonstrations import multi_demo,generated
from phdexlab.experiments import create,read,save
from phdexlab.integration import verify,file_hash
from phdexlab.paths import Layout
from phdexlab.multi_excel import sheet_name
from phdexlab.workspace import Window
from phdexlab.protocols import FE

def app():return QApplication.instance() or QApplication([])

def test_catalog_covers_notion_and_published_tfc():
    assert len(ALL)==15
    assert all(p['source'].startswith('https://doi.org/') for p in ALL)
    assert '10.38212/2224-6614.2748' in TFC['source'] and '10.1038/s41598-023-42418-1' in TFC['notes'] and TFC['equivalent']=='Quercetin'
    assert state(dict(protocol=CUPRAC,rows=generated(CUPRAC)))[0]=='draft'
    for p in (MOISTURE_ADAPT,ASH_ADAPT):assert state(dict(protocol=p,rows=generated(p)))[0]=='draft'

def test_all_demo_engines_ready():
    assays=multi_demo(True);assert len(assays)==10
    assert all(state(a)[0]=='ready' for a in assays)
    assert all({r['sample_id'] for r in a['rows'] if r['kind']=='sample'}=={'Variety A','Variety B','Variety C'} for a in assays)

def test_master_isolation_roundtrip_and_draft_preservation(tmp_path):
    assays=multi_demo(False);assays[-1]['rows'][0]['A_end']='pending measurement'
    root=create(tmp_path/'EXP-multi',assays);loaded=read(root);assert len(loaded)==5
    assert loaded[-1]['rows'][0]['A_end']=='pending measurement'
    wb=load_workbook(Layout(root).master)
    from phdexlab.compact_excel import table_values
    assert wb['_PhDexLab'].sheet_state=='veryHidden' and 'Overview' in wb
    assert len([ws for ws in wb if ws.sheet_state=='visible'])==1+2*len(assays)
    assert table_values(wb,'Index')[5][3]=='DRAFT'
    assert 'A01_FRAP_Data' in wb and 'A02_ABTS_Data' in wb
    formula=table_values(wb,'A02_ABTS_Processing')[4][2]
    assert 'A02_ABTS_Analysis' in formula and 'A01_FRAP' not in formula
    assert len(table_values(wb,'A05_TFC_Results'))==1
    wb.close();verify(root)

def test_save_all_retains_other_assay_and_rejects_stale(tmp_path):
    assays=multi_demo(False);root=create(tmp_path/'EXP-save',assays);before=(Layout(root).meta/'raw.initial.json').read_bytes();h=file_hash(Layout(root).master)
    with pytest.raises(RuntimeError,match='cambió'):save(root,assays,'old hash')
    assays[1]['rows'][0]['notes']='Edited only ABTS';save(root,assays,h);new=read(root)
    assert new[1]['rows'][0]['notes']=='Edited only ABTS' and new[0]['rows']==read(root)[0]['rows']
    assert (Layout(root).meta/'raw.initial.json').read_bytes()==before;verify(root)

def test_legacy_upgrade_preserves_initial_snapshots(tmp_path):
    from phdexlab.integration import create_experiment
    from phdexlab.data_entry import demo_rows
    root=create_experiment(tmp_path/'EXP-old',demo_rows());l=Layout(root);snap=(l.meta/'protocol.initial.json').read_bytes()
    assays=read(root);assays.append(copy.deepcopy(multi_demo(False)[1]));save(root,assays,file_hash(l.master))
    assert (l.meta/'protocol.initial.json').read_bytes()==snap
    assert verify(root)['schema']==3 and len(read(root))==2

def test_dpph_requires_matched_controls_and_confirmed_plateau():
    a=multi_demo(True)[5];p=a['protocol'];rows=a['rows']
    with pytest.raises(ValueError,match='control radical'):clean([r for r in rows if not(r['kind']=='blank' and r['time_min']==15)],p)
    changed=copy.deepcopy(rows);next(r for r in changed if r['kind']=='sample' and r['plateau'])['plateau']=False
    with pytest.raises(ValueError,match='sin meseta'):clean(changed,p)

def test_sieve_no_double_count_of_same_fraction():
    a=multi_demo(True)[-1];extra=copy.deepcopy(a['rows'][0]);extra.update(record_id='extra',tech_id='second weighing')
    with pytest.raises(ValueError,match='Una masa por fracción'):clean(a['rows']+[extra],a['protocol'])

def test_workspace_switch_preserves_unsaved_data_and_help():
    q=app();w=Window();w.load_multi_demo(False)
    w.raw.item(0,6).setText('0.031')
    w.assay_list.setCurrentRow(1);assert w.protocol()['method']=='ABTS'
    w.assay_list.setCurrentRow(0);assert w.raw.item(0,6).text()=='0.031'
    w.assay_list.setCurrentRow(1);assert w.raw.kind_names['blank']=='Control radical sin antioxidante'
    assert len(w.assays)==5 and w.help_dialog.topics.count()==13
    w.dirty=False;w.close()

def test_workspace_non_absorbance_forms():
    q=app();w=Window();w.load_multi_demo(True);w.assay_list.setCurrentRow(6)
    assert w.raw.columns[5:8]==['tare_g','initial_g','final_g']
    w.assay_list.setCurrentRow(5);assert 'dose_mg_mL' in w.raw.columns and 'plateau' in w.raw.columns
    w.assay_list.setCurrentRow(9);assert 'loaded_g' in w.raw.columns
    w.dirty=False;w.close()

def test_assay_numbers_not_reused_after_removal():
    q=app();w=Window();w.load_multi_demo(False);w.assay_list.setCurrentRow(4)
    with patch('phdexlab.workspace.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):w.remove_assay()
    aid=w.append_assay(TFC,'New TFC');assert aid.startswith('A06_');w.dirty=False;w.close()

def test_origin_open_blocks_stale_project_after_excel_only(tmp_path):
    from phdexlab.integration import dump
    q=app();root=create(tmp_path/'EXP-origin',multi_demo(False));l=Layout(root);l.project.write_bytes(b'old project')
    dump(l.meta/'status.json',dict(state='complete',assays={},origin=dict(state='skipped'),excel_sha256=file_hash(l.master)))
    w=Window();w.load_folder(root)
    with pytest.raises(ValueError,match='modo Origin'):w.open_origin()
    w.dirty=False;w.close()
