"""Acquisition choices and provenance, independent from scientific validation."""
import copy,os
from pathlib import Path
from unittest.mock import patch
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QMessageBox,QTableWidgetItem
from phdexlab import i18n
from phdexlab.method_catalog import ALL
from phdexlab.assay_engine import clean,cell_plan,required,columns,engine
from phdexlab.reading_design import configure,validate_groups,signal,prepare_row
from phdexlab.demonstrations import multi_demo,mean_demo,generated
from phdexlab.measurement_entry import MeasurementDialog
from phdexlab.multi_excel import write_master,read_master,sheet_name
from phdexlab.data_templates import make_template,instantiate

@pytest.fixture(autouse=True)
def isolate(tmp_path,monkeypatch):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'personal'));i18n.set_language('en')
    yield
    i18n.set_language('es')

def app():return QApplication.instance() or QApplication([])

@pytest.mark.parametrize('p',ALL,ids=lambda p:p['id'])
def test_every_catalogue_method_has_an_explicit_suitable_design(p):
    from phdexlab.assay_engine import validate_protocol
    validate_protocol(p);assert p['default_replicates']==(1 if engine(p)=='gravimetric' else 2 if p['id']=='tpc-folin' else 3)
    if engine(p) in ('gravimetric','sieve'):assert 'reading_basis' not in columns(p)
    else:
        assert p['matrix_mode']=='none' and 'matrix_blank_delta' not in required('sample',p)
        assert ('A_initial' in required('sample',p))==(signal(p)=='paired' and engine(p)=='colorimetric')

def test_mean_and_individual_are_exclusive_without_fake_replicates():
    a=mean_demo()[0];rows=clean(a['rows'],a['protocol']);assert len(rows)==16
    assert all(d['reading_basis']=='mean' and d['technical_n']==3 for d in rows)
    duplicate=copy.deepcopy(rows[-1]);duplicate['record_id']='extra';duplicate['tech_id']='another'
    with pytest.raises(ValueError,match='do not mix'):clean(rows+[duplicate],a['protocol'])
    duplicate['reading_basis']='individual';duplicate.update(technical_n=None,technical_sd=None)
    with pytest.raises(ValueError,match='do not mix'):validate_groups(rows+[duplicate],a['protocol'])

def test_unknown_precision_is_na_and_known_precision_has_auditable_raw_references():
    a=mean_demo(precision=False)[0];rows=clean(a['rows'],a['protocol']);f=cell_plan(rows,a['protocol'])
    assert f['Calibration']['C2']=='=NA()' and f['Calibration']['D2']=='=NA()'
    assert f['Results']['D2']=='=NA()' and f['Results']['F2']=='=NA()'
    a=mean_demo()[0];rows=clean(a['rows'],a['protocol']);f=cell_plan(rows,a['protocol'])
    assert f['Calibration']['C2'].startswith('=RAW!Q') and f['Calibration']['D2'].startswith('=RAW!R')
    assert 'ABS(' in f['Results']['F2'] and 'PRECOMPUTED MEAN' in f['Results']['H2']

@pytest.mark.parametrize('e',['inhibition','ec50'])
def test_absorbance_sd_is_converted_to_inhibition_sd(e):
    a=next(a for a in mean_demo() if engine(a['protocol'])==e);rows=clean(a['rows'],a['protocol']);f=cell_plan(rows,a['protocol'])
    expression=f['Calibration']['D2'] if e=='inhibition' else f['DoseCurve']['E2']
    assert '100/' in expression and 'RAW!' in expression

def test_no_initial_reading_for_endpoint_or_direct_delta():
    a=multi_demo()[0]
    for mode in ('endpoint','delta'):
        p=copy.deepcopy(a['protocol']);p.update(reading_signal=mode,response='endpoint' if mode=='endpoint' else 'delta')
        rows=copy.deepcopy(a['rows'])
        for row in rows:row['A_initial']=''
        result=clean(rows,p);assert cell_plan(result,p)['Processing']['B2']=='=RAW!G2'
    with pytest.raises(ValueError,match='faltan lecturas'):clean(rows,a['protocol'])

def test_disabled_sample_correction_never_discards_nonzero_measurements():
    a=multi_demo()[0];rows=copy.deepcopy(a['rows'])
    for row in rows:row['matrix_blank_delta']=''
    clean(rows,a['protocol']);rows[-1]['matrix_blank_delta']=.03
    with pytest.raises(ValueError,match='nonzero data'):clean(rows,a['protocol'])
    a['protocol']['matrix_mode']='net';rows[-1]['matrix_blank_delta']=0
    with pytest.raises(ValueError,match='matrix_blank_delta'):clean(rows,a['protocol'])

def test_zeroed_input_explicitly_uses_zero_without_inventing_a_blank_row():
    a=multi_demo()[0];p=a['protocol'];p.update(blank_handling='zeroed',reading_signal='endpoint',response='endpoint')
    rows=[r for r in a['rows'] if r['kind']!='blank'];result=clean(rows,p)
    assert all(r['kind']!='blank' for r in result) and cell_plan(result,p)['Calibration']['J2']=='=0'
    with pytest.raises(ValueError,match='conflicts'):clean(a['rows'],p)

@pytest.mark.parametrize('n,sd',[(0,None),(2.2,None),(-1,None),(1,0),(3,-.1)])
def test_invalid_reported_precision_is_rejected(n,sd):
    p=ALL[0];row=dict(reading_basis='mean',technical_n=n,technical_sd=sd)
    with pytest.raises(ValueError):prepare_row(row,p)

def test_legacy_protocol_remains_unchanged_until_explicit_upgrade():
    from phdexlab.protocols import FE
    old=copy.deepcopy(FE);new=configure(old,legacy=True)
    assert old==FE and 'reading_schema' not in old and new['matrix_mode']=='net'
    assert signal(new)==signal(old) and new['source']==old['source']

def test_all_mean_demo_methods_roundtrip_and_templates_clear_measured_sd(tmp_path):
    assays=mean_demo();path=tmp_path/'means.xlsx';write_master(path,assays,'TEST')
    reopened=read_master(path)
    for a in reopened:clean(a['rows'],a['protocol'])
    template=make_template('design',assays[0]['protocol'],assays[0]['rows'])
    assert all(r['A_end']=='' and r['technical_sd']=='' and r['technical_n']==3 for r in template['rows'])
    assert all(r['reading_basis']=='mean' for r in instantiate(template,assays[0]['protocol']))

def test_guided_entry_variable_readings_or_only_mean():
    q=app();d=MeasurementDialog(ALL[1]);d.name.setText('Variety A');d.count.setValue(7)
    assert d.grid.rowCount()==7 and d.grid.isColumnHidden(1)
    for r in range(7):d.grid.setItem(r,0,QTableWidgetItem(str(.3+r*.01)))
    p,rows=d.data();assert len(rows)==7 and all(r['reading_basis']=='individual' for r in rows)
    d.mode.setCurrentIndex(d.mode.findData('mean'));d.mean_inputs['A_end'][0].setText('.33')
    p,rows=d.data();assert len(rows)==1 and rows[0]['A_end']==.33 and rows[0]['technical_n'] is None
    d.n.setText('7');d.sd.setText('.02');p,rows=d.data();assert rows[0]['technical_n']==7 and rows[0]['technical_sd']==.02;d.reject()

def test_guided_entry_is_method_specific_for_mass_and_sieve():
    q=app()
    for e in ('gravimetric','sieve'):
        p=next(p for p in ALL if engine(p)==e);d=MeasurementDialog(p);d.name.setText('A')
        assert d.mode.count()==1 and 'A_end' not in d.keys
        if e=='sieve':assert d.keys==['lower_um','upper_um','retained_g']
        d.reject()

def test_view_hides_unused_columns_and_signal_change_with_readings_is_protected():
    from phdexlab.workspace import Window
    q=app();w=Window();w.append_assay(ALL[1],'FRAP endpoint');q.processEvents()
    assert w.raw.isColumnHidden(w.raw.columns.index('A_initial')) and w.raw.isColumnHidden(w.raw.columns.index('matrix_blank_delta'))
    assert not w.raw.isColumnHidden(w.raw.columns.index('reading_basis'))
    w.raw.setItem(0,6,QTableWidgetItem('.5'))
    row=next(r for r in range(w.parameters.rowCount()) if w.parameters.item(r,0).data(256)=='reading_signal');editor=w.parameters.cellWidget(row,1)
    with patch.object(QMessageBox,'information') as warning:editor.setCurrentIndex(editor.findData('paired'));assert warning.called
    assert editor.currentData()=='endpoint' and w.raw.item(0,6).text()=='.5'
    w.dirty=False;w.close()


def test_controls_use_known_concentration_once_and_calibration_minimum_is_configurable():
    a=multi_demo()[0];p=a['protocol']
    for row in a['rows']:
        if row['kind']=='control':row['concentration']=''
    clean(a['rows'],p);assert 'concentration' not in required('control',p)
    selected=[r for r in a['rows'] if r['kind']!='standard' or r['concentration'] in (100,300)]
    with pytest.raises(ValueError,match='tres niveles'):clean(selected,p)
    p['minimum_calibration_levels']=2;clean(selected,p)
    p['minimum_calibration_levels']=1
    with pytest.raises(ValueError,match='Calibration levels'):clean(selected,p)


def test_legacy_templates_upgrade_without_reusing_measured_precision():
    from phdexlab.protocols import FE
    from phdexlab.data_entry import demo_rows
    old=make_template('legacy',FE,demo_rows());rows=instantiate(old,ALL[0])
    assert all(r['reading_basis']=='individual' and r['technical_sd']=='' for r in rows)
    assert all(r['A_end']=='' for r in rows)


def test_mixed_entry_basis_between_independent_units_is_supported():
    a=multi_demo()[0];means=mean_demo()[0]
    rows=[r for r in a['rows'] if not (r['kind']=='sample' and r['bio_id']=='B1')]
    rows+=[r for r in means['rows'] if r['kind']=='sample' and r['bio_id']=='B1']
    for index,row in enumerate(rows):row['record_id']=f'X{index}'
    result=clean(rows,a['protocol']);assert any(r['reading_basis']=='mean' for r in result)
    assert any(r['reading_basis']=='individual' for r in result)


def test_explicit_legacy_ui_upgrade_keeps_raw_and_signal():
    from phdexlab.workspace import Window
    q=app();w=Window();w.load_demo();before=w.raw.records();p=w.protocol();w.configure_input_options()
    assert w.protocol()['reading_schema']==2 and signal(w.protocol())==signal(p) and w.dirty
    after=w.raw.records()
    assert all(all(old[k]==new[k] for k in old) for old,new in zip(before,after))
    w.dirty=False;w.close()


def test_unused_slots_are_not_required_measurements():
    q=app();d=MeasurementDialog(ALL[1]);d.name.setText('Sample')
    d.grid.setItem(0,0,QTableWidgetItem('.4'));d.grid.setItem(1,0,QTableWidgetItem('.5'))
    assert d.count.value()==3 and len(d.data()[1])==2
    d.reject()


def test_reagent_blank_cannot_silently_ignore_a_sample_correction():
    p=copy.deepcopy(ALL[0]);p['matrix_mode']='net'
    with pytest.raises(ValueError,match='reagent blank'):prepare_row(dict(kind='blank',reading_basis='individual',matrix_blank_delta=.02),p)


def test_legacy_book_writer_cannot_discard_mean_provenance(tmp_path):
    from phdexlab.excel import write_book
    a=mean_demo()[0]
    with pytest.raises(ValueError,match='experiments.create'):write_book(tmp_path/'legacy.xlsx',a['rows'],a['protocol'],'TEST')

def test_variant_change_preserves_legacy_readings_and_mean_provenance():
    from phdexlab.workspace import Window
    from phdexlab.protocols import FE
    q=app();w=Window();w.load_demo();original=w.raw.records()
    w.select_variant(w.variant.findData(0))
    assert w.protocol()['reading_schema']==2
    assert len(w.raw.records())==len(original)
    assert all(all(old[k]==new[k] for k in old) for old,new in zip(original,w.raw.records()))
    w.dirty=False;w.load_mean_demo();original=w.raw.records();w.variants.append(copy.deepcopy(FE));w.populate_variants(w.protocol())
    w.select_variant(w.variant.findData(len(w.variants)-1))
    assert len(w.raw.records())==len(original)
    assert all(all(old[k]==new[k] for k in old) for old,new in zip(original,w.raw.records()))
    w.dirty=False;w.close()
