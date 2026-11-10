"""Explicit Windows/Excel check. Run from the source root with PYTHONPATH set.

python tests/native_reading_validation.py NEW_EMPTY_OUTPUT_DIRECTORY
Synthetic data only. No Origin required for this numerical equivalence check.
"""
import copy,json,math,sys
from pathlib import Path
from phdexlab.demonstrations import multi_demo,mean_demo,generated
from phdexlab.method_catalog import ALL
from phdexlab.multi_excel import write_master,recalculate_master,sheet_name
from phdexlab.excel import values,value_session
from phdexlab.assay_engine import engine

@value_session
def validate(destination):
    destination=Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):raise FileExistsError('Choose a new or empty output directory')
    destination.mkdir(parents=True,exist_ok=True)
    groups={'individual':multi_demo(True),'mean':mean_demo(),'mean_unknown':mean_demo(precision=False)}
    books={}
    for label,assays in groups.items():
        path=destination/(label+'.xlsx');write_master(path,assays,'SYNTHETIC-EQUIVALENCE',calculated=True)
        recalculate_master(path,destination/(label+'-Excel'));books[label]=path
        print(label,'Excel recalculated',flush=True)
    # Independent expected mean across unitss for the synthetic designs.
    expected={'FRAP':[16,24,32],'ABTS':[12.12,24.24,36.36],'CUPRAC':[12,18,24],
        'TPC':[1.36096,1.7012,2.04144],'TFC':[.8,1.2,1.6],'DPPH':[.5,1,2],
        'HUMEDAD':[20,30,40],'MATERIA_SECA':[80,70,60],'CENIZAS':[5,6,7]}
    checks=0
    for a in groups['individual']:
        summaries={k:values(path,sheet_name(a,'Summary'))[1:] for k,path in books.items()}
        baseline=summaries['individual']
        for mode,data in summaries.items():
            assert len(data)==len(baseline)
            for old,new in zip(baseline,data):
                assert old[:2]==new[:2]
                for index in (2,3):
                    assert math.isclose(old[index],new[index],rel_tol=1e-9,abs_tol=1e-10),(a['id'],mode,index,old,new)
                    checks+=1
        if a['protocol']['method'] in expected:
            for row,wanted in zip(baseline,expected[a['protocol']['method']]):
                assert row[1]==3 and math.isclose(row[2],wanted,rel_tol=1e-9),(a['id'],row,wanted)
        if engine(a['protocol']) in ('colorimetric','inhibition'):
            old=values(books['individual'],sheet_name(a,'Results'))[1:]
            new=values(books['mean'],sheet_name(a,'Results'))[1:]
            for r,s in zip(old,new):
                assert r[3]==s[3]==3
                assert math.isclose(r[4],s[4],rel_tol=1e-9,abs_tol=1e-10)
                assert math.isclose(r[5],s[5],rel_tol=1e-8,abs_tol=1e-10),(a['id'],r,s)
            missing=values(books['mean_unknown'],sheet_name(a,'Results'))[1:]
            assert all(r[3]=='#N/A' and r[5]=='#N/A' for r in missing)
    # Original variants not represented by the 10-method example.
    variants=[]
    for p in ALL:
        if p['id'] in ('frap-trolox-draft','abts-adapted','tpc-adapted'):
            variants.append(dict(id=f'A{len(variants)+1:02}_{p["method"]}',label=p['name'],protocol=copy.deepcopy(p),rows=generated(p)))
    path=destination/'variants.xlsx';write_master(path,variants,'SYNTHETIC-VARIANTS',calculated=True);recalculate_master(path,destination/'variants-Excel')
    for a in variants:
        for row in values(path,sheet_name(a,'Summary'))[1:]:assert isinstance(row[2],(int,float)) and math.isfinite(row[2])
    # Direct ΔA input must produce the same numerical FRAP values as paired input.
    a=copy.deepcopy(groups['individual'][0]);a['protocol']['reading_signal']='delta'
    for row in a['rows']:row['A_end']-=row['A_initial'];row['A_initial']=''
    path=destination/'direct-delta.xlsx';write_master(path,[a],'SYNTHETIC-DELTA',calculated=True);recalculate_master(path,destination/'delta-Excel')
    for row,wanted in zip(values(path,sheet_name(a,'Summary'))[1:],expected['FRAP']):assert math.isclose(row[2],wanted,rel_tol=1e-9)
    report=dict(methods=10,additional_variants=len(variants),comparisons=checks,independent_means=True,
        supplied_mean_precision=True,unknown_precision_not_invented=True,direct_delta_matches_paired=True)
    (destination/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)

if __name__=='__main__':validate(sys.argv[1])
