import copy,json
import pytest
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QTableWidgetItem,QTableWidgetSelectionRange
from openpyxl import load_workbook
from phdexlab.fill_series import series
from phdexlab.data_table import RawTable
from phdexlab.demonstrations import multi_demo,mean_demo
from phdexlab.multi_excel import write_master,read_master
from phdexlab.compact_excel import mappings,table_values,cells
from phdexlab.excel_styles import selection,save_user_style,user_styles
from phdexlab.excel_style_dialog import ExcelStyleDialog
from phdexlab import i18n

@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'user'));i18n.set_language('en')
    yield
    i18n.set_language('es')

@pytest.mark.parametrize('seed,want',[
 (['P0','P1'],['P2','P3','P4']),(['P005','P010'],['P015','P020','P025']),
 (['P0'],['P1','P2','P3']),(['5'],['5','5','5']),(['0.1','0.2'],['0.3','0.4','0.5']),
 (['0,5','1,0'],['1,5','2,0','2,5']),(['10','8'],['6','4','2']),
 (['A','B'],['A','B','A']),(['P1','P3','P4'],['P1','P3','P4'])])
def test_series(seed,want):assert series(seed,3)==want

def table():
    a=multi_demo()[0];w=RawTable();w.set_protocol(a['protocol']);w.load(a['rows']);return w

def select(w,top,left,bottom,right):
    w.clearSelection();w.setCurrentCell(top,left);w.setRangeSelected(QTableWidgetSelectionRange(top,left,bottom,right),True)

def test_repeat_action_uses_unused_ids_preserves_source_and_leaves_new_measurements_empty():
    w=table();row=next(i for i,r in enumerate(w.records()) if r['kind']=='sample');before=copy.deepcopy(w.records());w.setCurrentCell(row,2)
    w.add_repeated_readings(2);after=w.records();assert len(after)==len(before)+2
    assert after[row]==before[row]
    new=after[row+1:row+3];assert all(r['A_end']=='' and r['sample_id']==before[row]['sample_id'] and r['bio_id']==before[row]['bio_id'] for r in new)
    assert {r['tech_id'] for r in new}=={'4','5'}
    assert len({r['record_id'] for r in after})==len(after)
    w.undo_cells();assert w.records()==before;w.redo_cells();assert len(w.records())==len(after)
    w.close()

def test_mean_cannot_be_replicated():
    a=mean_demo()[0];w=RawTable();w.set_protocol(a['protocol']);w.load(a['rows']);before=w.records();row=next(i for i,r in enumerate(before) if r.get('reading_basis')=='mean');w.setCurrentCell(row,2)
    with pytest.raises(ValueError,match='mean'):w.add_repeated_readings(2)
    assert w.records()==before;w.close()

def test_drag_fill_handle_and_undo_redo():
    w=table();w.resize(1000,700);w.show();col=w.columns.index('sample_id')
    w.setItem(0,col,QTableWidgetItem('P0'));w.setItem(1,col,QTableWidgetItem('P1'));QApplication.processEvents();w.reset_history();select(w,0,col,1,col);QApplication.processEvents()
    start=w.handle_rect().center();target=w.visualRect(w.model().index(4,col)).center()
    QTest.mousePress(w.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,start)
    QTest.mouseMove(w.viewport(),target);QTest.mouseRelease(w.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,target)
    assert [w.item(r,col).text() for r in range(5)]==['P0','P1','P2','P3','P4']
    QTest.keyClick(w,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier);assert w.item(2,col).text()!='P2'
    QTest.keyClick(w,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier);assert w.item(4,col).text()=='P4';w.close()

def test_fill_shortcuts_paste_selection_and_edit_history():
    w=table();c=w.columns.index('tech_id');select(w,0,c,3,c);w.setItem(0,c,QTableWidgetItem('7'));QApplication.processEvents();w.reset_history()
    QTest.keyClick(w,Qt.Key.Key_D,Qt.KeyboardModifier.ControlModifier);assert all(w.item(r,c).text()=='7' for r in range(4))
    w.undo_cells();assert w.item(1,c).text()!='7'
    select(w,0,c,2,c);w.paste('9');assert all(w.item(r,c).text()=='9' for r in range(3))
    w.undo_cells();assert w.item(0,c).text()=='7';w.close()

def test_compact_layout_roundtrip_formula_count_charts_and_legacy_import(tmp_path):
    a=multi_demo(True);old=tmp_path/'old.xlsx';new=tmp_path/'new.xlsx'
    write_master(old,a,'E',compact_layout=False);write_master(new,read_master(old),'E')
    oldwb=load_workbook(old);newwb=load_workbook(new)
    try:
        assert len([w for w in newwb if w.sheet_state=='visible'])==1+2*len(a)
        assert [w.title for w in newwb if w.sheet_state!='visible']==['_PhDexLab']
        assert all(table_values(oldwb,a0['id']+'_RAW')==table_values(newwb,a0['id']+'_RAW') for a0 in a)
        count=lambda wb:sum(c.data_type=='f' for w in wb for row in w for c in row)
        assert count(oldwb)==count(newwb)
        names=set(newwb.sheetnames)
        from openpyxl.formula.tokenizer import Tokenizer
        for ws in newwb:
            for row in ws:
                for c in row:
                    if c.data_type=='f':
                        for token in Tokenizer(c.value).items:
                            if token.subtype=='RANGE' and '!' in token.value:assert token.value.rsplit('!',1)[0].strip("'") in names
        assert sum(len(w._charts) for w in oldwb)==sum(len(w._charts) for w in newwb)
        from openpyxl.xml.functions import tostring
        for ws in newwb:
            for chart in ws._charts:
                xml=tostring(chart._write()).decode()
                assert '_Summary!' not in xml and '_Calibration!' not in xml and '_Summary&amp;' not in xml
                assert '_Analysis' in xml
        assert read_master(old)==read_master(new)
    finally:oldwb.close();newwb.close()

def test_style_customisation_preview_persistence_and_actual_workbook(tmp_path):
    value=selection(dict(preset='green',font='Arial',font_size=12,row_height=24,header='#123456',accent='#AA3344'))
    save_user_style('Reusable workbook',value);assert user_styles()[0]['settings']==value
    d=ExcelStyleDialog(value);d.show();QApplication.processEvents();assert d.preview.font().family()=='Arial' and d.preview.rowHeight(0)==24
    assert '#AA3344' in d.preview_title.styleSheet();d.preset.setCurrentIndex(1);assert d.selected['preset']=='blue'
    d.stripe.setChecked(False);assert d.selected['striped'] is False;d.reject()
    a=multi_demo()[:1];path=tmp_path/'styled.xlsx';write_master(path,a,'Style',excel_style=value);wb=load_workbook(path)
    try:
        raw=cells(wb,a[0]['id']+'_RAW');assert raw[0][1].fill.fgColor.rgb.endswith('123456')
        assert raw[1][1].font.name=='Arial' and raw[1][1].font.sz==12
        assert wb[raw[0][1].parent.title].row_dimensions[raw[1][1].row].height==24
        sample=next(i for i,r in enumerate(a[0]['rows']) if r['kind']=='sample')
        raw[sample+1][6].value=.987654321;wb.save(path)
        assert read_master(path)[0]['rows'][sample]['A_end']==.987654321
    finally:wb.close()


def test_number_existing_rows_groups_samples_and_preserves_values():
    w=table();before=w.records();start=next(i for i,r in enumerate(before) if r['kind']=='sample')
    select(w,start,2,start+5,2);w.number_repeated_readings();after=w.records()
    assert [r['tech_id'] for r in after[start:start+6]]==['1','2','3','1','2','3']
    assert all({k:v for k,v in a.items() if k!='tech_id'}=={k:v for k,v in b.items() if k!='tech_id'} for a,b in zip(before,after));w.close()
