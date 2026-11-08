from phdexlab.paths import Layout
import copy
import json
import pytest
from phdexlab.data_entry import demo_rows,normalize,number,parse_tsv,COLUMNS
from phdexlab.protocols import FE,TROLOX,validate,save_variant,digest
from phdexlab.integration import create_experiment,verify,preflight,locked,refresh,file_hash
from phdexlab.excel import read_inputs
from openpyxl import load_workbook

def test_demo_structure():
    rows=preflight(demo_rows(),FE)
    assert len(rows)==27
    assert len({r['bio_id'] for r in rows if r['kind']=='sample'})==2

@pytest.mark.parametrize('value',['nan','inf','-inf','1e999'])
def test_nonfinite_rejected(value):
    with pytest.raises(ValueError):number(value)

def test_decimal_comma_and_zero():
    assert number('0,00')==0
    assert number('') is None
    assert number(' 1,25 ')==1.25

@pytest.mark.parametrize('change',[
    {'record_id':'R0001'}, {'A_initial':''},{'matrix_blank_delta':''},
    {'dilution':0},{'mass_g':-1},{'extract_mL':''}, {'kind':'unknown'}])
def test_bad_input_rejected(change):
    rows=demo_rows();rows[18].update(change)
    with pytest.raises(ValueError):normalize(rows,FE)

def test_inconsistent_technical_parameters():
    rows=demo_rows();rows[18]['dilution']=3
    with pytest.raises(ValueError,match='parámetros distintos'):normalize(rows,FE)

def test_duplicate_technical_rep():
    rows=demo_rows();rows[19]['tech_id']='1'
    with pytest.raises(ValueError,match='duplicada'):normalize(rows,FE)

def test_no_blank_no_calibration():
    for rows in ([r for r in demo_rows() if r['kind']!='blank'],[r for r in demo_rows() if r['concentration'] not in (100,300,500)]):
        with pytest.raises(ValueError):preflight(rows,FE)

def test_protocol_unit_guard():
    p=dict(FE,concentration_unit='mg/L')
    with pytest.raises(ValueError):validate(p)
    validate(TROLOX)

def test_variant_immutable(tmp_path):
    a=save_variant(tmp_path,FE);old=a.read_bytes()
    b=save_variant(tmp_path,dict(FE,time_min=8,version=2))
    assert a!=b and a.read_bytes()==old
    assert save_variant(tmp_path,FE)==a

def test_roundtrip_and_input_integrity(tmp_path):
    folder=create_experiment(tmp_path/'exp',demo_rows())
    original=(Layout(folder).meta/'raw.initial.json').read_bytes()
    rows,p=read_inputs(Layout(folder).master);assert len(rows)==27;assert p==FE
    assert verify(folder)['raw_hash']==digest(json.loads(original))
    with pytest.raises(FileExistsError):create_experiment(folder,demo_rows())
    assert (Layout(folder).meta/'raw.initial.json').read_bytes()==original
    (Layout(folder).meta/'raw.initial.json').write_text('[]')
    with pytest.raises(ValueError,match='alterado'):verify(folder)

def test_formula_injection_stored_as_text(tmp_path):
    rows=demo_rows();rows[0]['notes']='=HYPERLINK("http://example.com")'
    folder=create_experiment(tmp_path/'exp',rows)
    book=load_workbook(Layout(folder).master);assert book['RAW']['N2'].data_type=='s';book.close()
    read_inputs(Layout(folder).master)

def test_formulas_in_inputs_rejected(tmp_path):
    folder=create_experiment(tmp_path/'exp',demo_rows());book=load_workbook(Layout(folder).master)
    book['RAW']['G2']='=1+1';book.save(Layout(folder).master);book.close()
    with pytest.raises(ValueError,match='no fórmulas'):read_inputs(Layout(folder).master)

def test_workflow_lock(tmp_path):
    with locked(tmp_path):
        with pytest.raises(RuntimeError):
            with locked(tmp_path):pass
    assert not (Layout(tmp_path).meta/'.workflow.lock').exists()

def test_stale_gui_detected_before_excel(tmp_path):
    folder=create_experiment(tmp_path/'exp',demo_rows())
    with pytest.raises(RuntimeError,match='cambió'):refresh(folder,expected_hash='obsolete')

def test_tsv_header():
    text='\t'.join(COLUMNS)+'\n'+'\t'.join(str(demo_rows()[0][k]) for k in COLUMNS)
    assert parse_tsv(text)[0]['record_id']=='R0001'
