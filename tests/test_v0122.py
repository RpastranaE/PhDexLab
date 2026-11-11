import copy
import pytest
from PySide6.QtCore import Qt,QMimeData,QPointF,QPoint
from PySide6.QtGui import QDragEnterEvent,QDragMoveEvent,QDropEvent,QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from phdexlab import i18n
from phdexlab import delimited_import as parser
from phdexlab.import_dialog import ImportDialog,MIME
from phdexlab.method_catalog import ALL
from phdexlab.reading_design import configure


def endpoint():
    p=configure(copy.deepcopy(ALL[0]));p.update(reading_signal='endpoint',response='endpoint',matrix_mode='none')
    return p


@pytest.mark.parametrize('lang',['es','en'])
def test_external_spanish_headings_and_short_types_do_not_depend_on_ui_language(lang):
    i18n.set_language(lang);p=endpoint()
    titles,rows,_=parser.parse('Origen de la lectura;Absorbancia - AU;Tipo de lectura;Factor de dilución previa - x;Concentración del patrón - µmol/L\nSpectrometer;0.2;Patrón;;100\nSpectrometer;0.3;Muestra;5;\nSpectrometer;0.01;Blanco;;\nSpectrometer;0.4;Control;;')
    mapping=parser.guess(titles,parser.import_fields(p),p)
    assert mapping=={'kind':2,'A_end':1,'dilution':3,'concentration':4}
    data=parser.records(rows,mapping,p)
    assert [r['kind'] for r in data]==['standard','sample','blank','control']
    assert data[1]['dilution']=='5' and data[0]['concentration']=='100'
    assert all(r['reading_basis']=='individual' for r in data)


@pytest.mark.parametrize('p',ALL)
def test_import_fields_follow_method_and_entered_signal(p):
    from phdexlab.assay_engine import engine
    from phdexlab.reading_design import signal,matrix_mode
    fields=parser.import_fields(p)
    assert ('A_initial' in fields)==(engine(p)=='colorimetric' and signal(p)=='paired')
    if matrix_mode(p)=='none':assert 'matrix_blank_delta' not in fields
    if engine(p) in ('gravimetric','sieve'):assert 'A_end' not in fields


def test_endpoint_paired_and_delta_dialog_labels(tmp_path):
    path=tmp_path/'data.csv';path.write_text('abs\n0.2',encoding='utf-8')
    for value in ('endpoint','paired','delta'):
        p=endpoint();p.update(reading_signal=value,response='endpoint' if value=='endpoint' else 'delta')
        d=ImportDialog(path,p)
        assert ('A_initial' in d.fields)==(value=='paired')
        assert ('final' in d.field_label('A_end').lower())==(value=='paired')
        assert 'matrix_blank_delta' not in d.fields
        assert 'origen' not in d.field_label('reading_basis').lower()
        d.close()


def test_native_drop_route_accepts_both_field_label_and_combo(tmp_path):
    path=tmp_path/'data.csv';path.write_text('Unknown\n0.2',encoding='utf-8');d=ImportDialog(path,endpoint());d.show();QApplication.processEvents()
    mime=QMimeData();mime.setData(MIME,b'0')
    box=d.combos['A_end'];pos=box.rect().center()
    for event in (QDragEnterEvent(pos,Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier),QDragMoveEvent(pos,Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier),QDropEvent(QPointF(pos),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)):
        QApplication.sendEvent(box,event);assert event.isAccepted()
    assert d.mapping['A_end']==0
    d.assign('A_end',-1)  # Invalid source is ignored.
    pos=d.targets.visualRect(d.targets.model().index(d.fields.index('sample_id'),0)).center()
    for event in (QDragEnterEvent(pos,Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier),QDropEvent(QPointF(pos),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)):
        QApplication.sendEvent(d.targets.viewport(),event);assert event.isAccepted()
    assert d.mapping['sample_id']==0;d.close()


@pytest.mark.parametrize('lang',['es','en'])
@pytest.mark.parametrize('field,value,code',[('kind','mystery','kind'),('A_end','0,3','number'),('A_end','1e999','finite'),('reading_basis','Spectrometer','basis'),('plateau','maybe','boolean')])
def test_errors_name_the_data_row_field_value_and_a_short_fix(lang,field,value,code):
    i18n.set_language(lang);p=endpoint()
    if field=='plateau':p=next(p for p in ALL if p.get('engine')=='ec50')
    with pytest.raises(parser.ImportProblem) as caught:parser.records([[value]],{field:0},p)
    error=caught.value;assert error.code==code and error.row==1 and error.field==field
    text=parser.error_text(error)
    assert ('Fila de datos 1' if lang=='es' else 'Data row 1') in text and value in text
    assert len(text)<300


def test_bad_format_cannot_reenable_import_and_late_error_is_atomic(tmp_path):
    i18n.set_language('es');path=tmp_path/'data.csv';path.write_text('A_end\n'+'0.2\n'*100+'bad\n',encoding='utf-8')
    d=ImportDialog(path,endpoint());assert d.import_button.isEnabled()
    d.accept();assert d.result_rows==[] and not d.import_button.isEnabled()
    assert '101' in d.status.text() and 'bad' in d.status.text()
    d.custom.setText(';');d.options['delimiter'].setCurrentIndex(d.options['delimiter'].findData('custom'))
    path.write_text('sample;abs\nA;0.2;extra',encoding='utf-8');d.reload();assert not d.import_button.isEnabled()
    d.unit.setText('New unit');assert not d.import_button.isEnabled();d.accept();assert d.result_rows==[]
    d.close()


def test_auto_delimiter_rejects_inconsistent_rows_instead_of_importing_one_column():
    with pytest.raises(parser.ImportProblem) as caught:parser.parse('sample;abs\nA;0.2\nB;0.3;extra')
    assert caught.value.code=='columns' and caught.value.row==2


def test_drag_starts_from_a_header_or_source_cells(tmp_path,monkeypatch):
    path=tmp_path/'data.csv';path.write_text('First;Second\nA;0.2',encoding='utf-8');d=ImportDialog(path,endpoint());d.show();QApplication.processEvents()
    started=[];monkeypatch.setattr(d.source,'start_column_drag',started.append)
    header=d.source.horizontalHeader();pos=QPoint(header.sectionViewportPosition(1)+header.sectionSize(1)//2,header.height()//2)
    QTest.mousePress(header.viewport(),Qt.MouseButton.LeftButton,pos=pos)
    move=QMouseEvent(QMouseEvent.Type.MouseMove,QPointF(pos+QPoint(30,0)),QPointF(header.viewport().mapToGlobal(pos+QPoint(30,0))),Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(header.viewport(),move)
    QTest.mouseRelease(header.viewport(),Qt.MouseButton.LeftButton,pos=pos)
    d.source.setCurrentCell(0,0);d.source.startDrag(Qt.DropAction.CopyAction)
    assert started==[1,0];d.close()


def test_binary_empty_bad_quotes_and_incompatible_method_have_actionable_errors(tmp_path):
    path=tmp_path/'data.xlsx';path.write_bytes(b'PK\x03\x04binary')
    with pytest.raises(parser.ImportProblem) as caught:parser.read_text(path)
    assert caught.value.code=='text'
    path=tmp_path/'empty.csv';path.write_text('',encoding='utf-8')
    d=ImportDialog(path,endpoint());assert not d.import_button.isEnabled() and ('datos' in d.status.text() or 'data' in d.status.text());d.close()
    import csv
    with pytest.raises(csv.Error) as caught:parser.parse('sample;abs\n"unfinished;0.2',';')
    assert ('comillas' in parser.error_text(caught.value).lower() or 'quotes' in parser.error_text(caught.value).lower())
    p=next(p for p in ALL if p.get('engine')=='ec50')
    with pytest.raises(parser.ImportProblem) as caught:parser.records([['Patrón']],{'kind':0},p)
    assert caught.value.code=='method_kind'
