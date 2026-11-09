import copy
import pytest
from openpyxl import load_workbook
from phdexlab.assay_engine import clean,ready_protocol
from phdexlab.method_catalog import ALL
from phdexlab.demonstrations import multi_demo
from phdexlab.multi_excel import write_master


def test_multiple_dilutions_share_one_independent_extraction():
    a=multi_demo()[0];rows=a['rows'];sample=next(r for r in rows if r['kind']=='sample')
    extra=dict(sample,record_id='another-dilution',dilution=10)
    result=clean(rows+[extra],a['protocol'])
    assert len(result)==len(rows)+1
    with pytest.raises(ValueError,match='duplicada'):clean(rows+[dict(extra,dilution=sample['dilution'])],a['protocol'])
    with pytest.raises(ValueError,match='parámetros distintos'):clean(rows+[dict(extra,mass_g=.25)],a['protocol'])


def test_control_must_not_silently_ignore_extraction_inputs():
    a=multi_demo()[0];control=next(r for r in a['rows'] if r['kind']=='control');control['mass_g']=.5
    with pytest.raises(ValueError,match='control|quality control'):clean(a['rows'],a['protocol'])


@pytest.mark.parametrize('method',['HUMEDAD','MATERIA_SECA','CENIZAS','DPPH','GRANULOMETRIA'])
def test_numerical_percentages_cannot_be_relabelled_as_equivalents(method):
    p=copy.deepcopy(next(p for p in ALL if p['method']==method));p['result_unit']='umol TE/g'
    with pytest.raises(ValueError):ready_protocol(p)


def test_tfc_source_mass_basis_and_explicit_ec50_adaptation():
    p=next(p for p in ALL if p['method']=='TFC');assert p['mass_basis']=='dry extract'
    assert '10 mg' in p['notes'] and '4 mL' in p['notes']
    assert 'molar-ratio' in next(p for p in ALL if p['method']=='DPPH')['notes']


def test_processing_exposes_normalisation_chain_without_percentage_format(tmp_path):
    path=tmp_path/'audit.xlsx';write_master(path,multi_demo(True),'AUDIT')
    wb=load_workbook(path)
    try:
        ws=wb['A01_FRAP_Processing'];raw=wb['A01_FRAP_RAW']
        for r in range(2,raw.max_row+1):
            if raw.cell(r,2).value=='sample':
                assert ws.cell(r,5).value==f'=M{r}/K{r}*L{r}'
                assert ws.cell(r,6).value=='umol eq Fe(II)/g'
                assert ws.cell(r,10).value==f"='A01_FRAP_RAW'!K{r}/1000"
                assert '%' not in ws.cell(r,5).number_format
            elif raw.cell(r,2).value=='control':assert ws.cell(r,6).value=='% recovery'
        assert wb['A06_DPPH_Processing']['C2'].value=='=100*(1-B2/G2)'
        assert 'Net initial' in wb['A07_HUMEDAD_Processing']['C1'].value
    finally:wb.close()


def test_legacy_frap_writer_retains_normalisation_labels_and_units(tmp_path):
    from phdexlab.excel import write_book
    from phdexlab.data_entry import demo_rows
    from phdexlab.protocols import FE
    path=tmp_path/'legacy.xlsx';rows=demo_rows();write_book(path,rows,FE,'LEGACY')
    wb=load_workbook(path)
    try:
        assert wb['Processing']['J1'].value=='Total extract volume (L)'
        for i,row in enumerate(rows,2):
            if row['kind']=='sample':assert wb['Processing'].cell(i,6).value==FE['result_unit']
    finally:wb.close()
