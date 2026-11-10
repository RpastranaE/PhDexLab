import xml.etree.ElementTree as ET
import pytest
from openpyxl import load_workbook
from PySide6.QtWidgets import QApplication
from phdexlab.excel_styles import selection
from phdexlab.excel_style_dialog import ExcelStyleDialog
from phdexlab.multi_excel import write_master
from phdexlab.compact_excel import cells
from phdexlab.demonstrations import multi_demo
from phdexlab.origin_export import cleaned_svg, SVG


def test_extended_style_controls_match_workbook_and_preserve_formulas(tmp_path):
    style=selection(dict(preset='violet',header_text='#FFFFAA',text='#112233',background='#FAF8F4',
        border='all',border_color='#AA3344',alignment='right',header_size=15,section_size=18,
        title_size=22,header_height=80,column_scale=125,gridlines=True,striped=False))
    d=ExcelStyleDialog(style);d.show();QApplication.processEvents()
    assert d.preview.horizontalHeader().height()==80
    assert d.preview.columnWidth(0)==162
    assert d.preview.item(0,0).foreground().color().name()=='#112233'
    assert d.preview.item(0,0).background().color().name()=='#faf8f4'
    d.controls['section_size'].setValue(20);assert '20pt' in d.section_title.styleSheet()
    from phdexlab.interface import STYLE
    d.setStyleSheet(STYLE);d.font.setCurrentText('Times New Roman');QApplication.processEvents()
    assert d.preview.font().family()=='Times New Roman'
    assert 'font-family:"Times New Roman"' in d.preview.horizontalHeader().styleSheet()
    d.reject()
    assays=multi_demo()[:1];base=tmp_path/'base.xlsx';custom=tmp_path/'custom.xlsx'
    write_master(base,assays,'E');write_master(custom,assays,'E',excel_style=style)
    a=load_workbook(base);b=load_workbook(custom)
    try:
        for role in ('RAW','Parameters','Summary','Results','Calibration','Processing'):
            logical=assays[0]['id']+'_'+role
            # Every logical value/formula remains identical when only appearance changes.
            assert [[c.value for c in r] for r in cells(a,logical)]==[[c.value for c in r] for r in cells(b,logical)]
        raw=cells(b,assays[0]['id']+'_RAW');header=raw[0][1];body=raw[1][1]
        assert header.font.sz==15 and header.font.color.rgb.endswith('FFFFAA')
        assert body.border.bottom.style=='thin' and body.border.left.color.rgb.endswith('AA3344')
        assert body.alignment.horizontal=='right' and body.parent.sheet_view.showGridLines is True
        assert body.parent.row_dimensions[header.row].height==80
        assert b['Overview']['A2'].font.sz==22
    finally:a.close();b.close()


@pytest.mark.parametrize('key,value',[('border','invalid'),('header_size',30),('column_scale',0),('gridlines','yes'),('background','red')])
def test_style_validation(key,value):
    with pytest.raises(ValueError):selection({key:value})


def test_svg_superscript_is_portable_and_punctuation_and_paths_unchanged():
    raw=('<svg xmlns="'+SVG+'"><path id="fit" d="M 1 2 L 3 4"/>'
         '<text font-size="40" transform="rotate(-90)"><tspan x="0 20 40 60">FRAP (µmol g⁻¹); x²; -1!</tspan></text></svg>').encode()
    result,count=cleaned_svg(raw,[]);assert count==0
    root=ET.fromstring(result);assert ''.join(root.itertext())=='FRAP (µmol g-1); x2; -1!'
    supers=[n for n in root.iter() if n.get('font-size')=='28']
    assert [n.text for n in supers]==['-1','2']
    assert all(n.get('y')=='-16.0' and n.tag=='{'+SVG+'}text' for n in supers)
    assert all(n.get('transform')=='rotate(-90)' for n in root if n.tag=='{'+SVG+'}text')
    assert next(root.iter('{'+SVG+'}path')).get('d')=='M 1 2 L 3 4'
    assert cleaned_svg(result,[])==(result,0)
