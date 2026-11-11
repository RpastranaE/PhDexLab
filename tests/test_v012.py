import copy
import pytest
from openpyxl import load_workbook
from PySide6.QtCore import Qt,QMimeData,QPointF,QPoint,QEvent
from PySide6.QtGui import QDragEnterEvent,QDropEvent
from PySide6.QtWidgets import QApplication
from phdexlab.delimited_import import parse,records,numeric,read_text,guess
from phdexlab.demonstrations import multi_demo
from phdexlab.import_dialog import ImportDialog,MIME
from phdexlab.compact_excel import rewrite,mappings,table_values
from phdexlab.multi_excel import write_master,read_master


@pytest.mark.parametrize('text,delimiter,decimal,thousands,expected',[
    ('Sample;Abs\nOlive;0,543',';',',','', '0.543'),
    ('Sample,Abs\nOlive,"1,234.56"',',','.',',','1234.56'),
    ('Sample\tAbs\nOlive\t1.234,56','\t',',','.','1234.56'),
    ('Sample|Abs\nOlive|-1.2e-3','|','.','','-1.2e-3')])
def test_text_conventions_and_mapping_without_column_order(text,delimiter,decimal,thousands,expected):
    titles,data,_=parse(text,delimiter);p=multi_demo()[0]['protocol']
    rows=records(data,{'sample_id':0,'A_end':1},p,decimal=decimal,thousands=thousands)
    assert rows[0]['A_end']==expected and rows[0]['sample_id']=='Olive'


def test_bom_quotes_skip_no_header_ids_and_repetitions(tmp_path):
    path=tmp_path/'unicode.txt';path.write_text('Instrument export\nSample;Abs\n"Olive; α";0,4\n"Olive; α";0,5',encoding='utf-16')
    titles,data,_=parse(read_text(path),';',1)
    p=multi_demo()[0]['protocol'];r=records(data,{'sample_id':0,'A_end':1},p,decimal=',')
    assert [v['tech_id'] for v in r]==['1','2']
    assert r[0]['sample_id']=='Olive; α'
    more=records([['Olive; α','0,6']],{'sample_id':0,'A_end':1},p,existing=r,decimal=',')
    assert more[0]['tech_id']=='3'
    assert parse('001;0.4',';',header=False)[1]==[['001','0.4']]
    assert records([['=1+1','0.4']],{'sample_id':0,'A_end':1},p)[0]['sample_id']=='=1+1'


@pytest.mark.parametrize('value,decimal,thousands',[('1,2','.', ''),('12,34.5','.',','),('NaN','.',''),('1,2',',',','),('1e999','.','')])
def test_invalid_numbers_are_never_silently_changed(value,decimal,thousands):
    with pytest.raises(ValueError):numeric(value,decimal,thousands)


def test_dialog_drag_mapping_preview_and_atomic_import(tmp_path):
    p=multi_demo()[0]['protocol'];path=tmp_path/'instrument.csv';path.write_text('Instrument response;Sample code\n0,45;001\n0,55;002',encoding='utf-8')
    d=ImportDialog(path,p);d.show();QApplication.processEvents()
    d.options['delimiter'].setCurrentIndex(d.options['delimiter'].findData(';'));d.options['decimal'].setCurrentIndex(d.options['decimal'].findData(','))
    # Deliver the same MIME/drop events as a dragged source header onto an arbitrary destination field.
    target=d.fields.index('A_end');pos=d.targets.visualRect(d.targets.model().index(target,0)).center()
    mime=QMimeData();mime.setData(MIME,b'0')
    enter=QDragEnterEvent(QPoint(pos),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(d.targets.viewport(),enter)
    drop=QDropEvent(QPointF(pos),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(d.targets.viewport(),drop);assert drop.isAccepted() and d.mapping['A_end']==0
    assert d.assign('sample_id',1);assert d.import_button.isEnabled()
    d.tabs.setCurrentIndex(1);QApplication.processEvents()
    d.accept();assert [r['sample_id'] for r in d.result_rows]==['001','002']
    assert [r['A_end'] for r in d.result_rows]==['0.45','0.55'];d.close()


def test_workbook_route_local_references_no_panes_and_overview(tmp_path):
    assays=multi_demo()[:2];path=tmp_path/'route.xlsx';write_master(path,assays,'E');wb=load_workbook(path)
    try:
        assert wb.active.title=='Overview'
        assert all(ws.freeze_panes is None for ws in wb)
        assert wb['A01_FRAP_Analysis']['A4'].value=='Calculation route'
        assert wb['A01_FRAP_Analysis']['A5'].hyperlink
        for a in assays:
            proc=table_values(wb,a['id']+'_Processing');assert proc[0][0]=='Reading (sample / unit / repeat)'
            assert '" / "' in proc[1][0]
            for ws in (wb[a['id']+'_Analysis'],):
                for row in ws:
                    for cell in row:
                        if cell.data_type=='f':assert "'"+ws.title+"'!" not in cell.value
        old=tmp_path/'legacy.xlsx';write_master(old,assays,'E',compact_layout=False)
        assert read_master(path)==read_master(old)
    finally:wb.close()


def test_rewrite_keeps_cross_sheet_names_and_chart_references():
    layout={'P':dict(sheet='Analysis',row=20,col=1),'C':dict(sheet='Analysis',row=4,col=1),'R':dict(sheet='Data',row=4,col=1)}
    assert rewrite('=C!$A$2+R!B2',layout,'P',local=True)=="=$A$5+'Data'!B5"
    assert rewrite('=C!$A$2',layout,'P')=="='Analysis'!$A$5"


def test_repeated_import_continues_after_excel_normalises_numeric_types():
    p=multi_demo()[0]['protocol'];p['default_dilution']=1.0
    old=records([['001','0.4']],{'sample_id':0,'A_end':1},p)
    old[0]['dilution']='1'
    new=records([['001','0.5']],{'sample_id':0,'A_end':1},p,existing=old)
    assert new[0]['tech_id']=='2'


def test_workspace_import_is_draft_safe_and_provenance_is_saved(tmp_path,monkeypatch):
    import hashlib,json
    from phdexlab import workspace
    from phdexlab.experiments import create
    from phdexlab.paths import Layout
    source=tmp_path/'instrument.csv';source.write_text('sample_id;A_end\nImported sample;0.45',encoding='utf-8')
    root=create(tmp_path/'EXP',multi_demo()[:1]);w=workspace.Window();w.load_folder(root)
    before=len(w.raw.records());monkeypatch.setattr(workspace.QFileDialog,'getOpenFileName',lambda *a,**k:(str(source),''))
    class Accepted(ImportDialog):
        def exec(self):self.accept();return self.DialogCode.Accepted
    monkeypatch.setattr(workspace,'ImportDialog',Accepted);w.import_readings()
    assert len(w.raw.records())==before+1 and w.dirty
    w.save(prompt_after_create=False)
    event=[json.loads(line) for line in (Layout(root).meta/'audit.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(line)['event']=='imported_delimited'][-1]
    assert event['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    assert event['count']==1 and event['mapping']['A_end']==1
    assert w.raw.records()[-1]['sample_id']=='Imported sample';w.dirty=False;w.close()
