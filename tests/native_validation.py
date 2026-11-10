from phdexlab.paths import Layout
"""Run explicitly on Windows desktop. Uses real Excel/Origin, synthetic data only.

python tests/native_validation.py TARGET_FOLDER
The folder must not exist. Evidence is saved as native_validation.json.
"""
import copy
import json
import math
import sys
from pathlib import Path
from openpyxl import load_workbook
from phdexlab.data_entry import demo_rows
from phdexlab.protocols import FE,TROLOX
from phdexlab.integration import create_experiment,refresh,verify,file_hash
from phdexlab.excel import values,read_inputs

def close(a,b):
    assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9),(a,b)

def run(target):
    root=Path(target);root.mkdir(parents=True,exist_ok=False)
    evidence=[]
    def record(case,**kw):evidence.append(dict(case=case,passed=True,**kw))
    folder=create_experiment(root/'fe',demo_rows(),FE)
    initial=(Layout(folder).meta/'raw.initial.json').read_bytes()
    report=refresh(folder,'connector');assert report['state']=='complete',report
    rs=values(Layout(folder).master,'Results');summary=values(Layout(folder).master,'Summary')
    close(rs[1][4],16);close(rs[2][4],24);close(rs[3][4],100)
    close(summary[1][2],20);close(summary[1][3],math.sqrt(32));assert summary[1][1]==2
    record('Fe independent arithmetic',bio_results=[16,24],biological_n=2,mean=20,sd=math.sqrt(32),origin=report['origin'])
    # Edit the master as a user would, including a new independent unit.
    wb=load_workbook(Layout(folder).master);ws=wb['RAW']
    for r in range(2,ws.max_row+1):
        if ws.cell(r,2).value=='sample' and ws.cell(r,4).value=='B1':ws.cell(r,10,4)
    last=ws.max_row+1
    template=[ws.cell(23,c).value for c in range(1,15)]
    for tech in (1,2):
        v=list(template);v[0]=f'new-{tech}';v[3]='B3';v[4]=str(tech);v[6]=0.53
        ws.append(v)
    wb.save(Layout(folder).master);wb.close()
    report=refresh(folder,'connector');assert report['state']=='complete',report
    rs=values(Layout(folder).master,'Results');summary=values(Layout(folder).master,'Summary')
    # B1: 400*4*.01/.5=32; B2=24; B3:500*2*.01/.5=20; equal weight mean across units.
    close(rs[1][4],32);close(summary[1][2],76/3);assert summary[1][1]==3
    assert (Layout(folder).meta/'raw.initial.json').read_bytes()==initial
    verify(folder);record('Excel manual edit + appended rows + existing Origin refresh',expected_mean=76/3,origin=report['origin'])
    # Alternative refresh preserving the existing graph objects after disconnecting DC.
    report=refresh(folder,'values');assert report['state']=='complete',report
    record('Origin values fallback',origin=report['origin'])
    # Calibration FINAL basis: standard concentrations /34, same response; must recover same amount.
    rows=demo_rows()
    for d in rows:
        if d['kind'] in ('standard','control'):
            d['concentration']=float(d['concentration'])/34
            if d['kind']=='control':d['expected']=float(d['expected'])/34
    final=create_experiment(root/'final_basis',rows,dict(FE,calibration_basis='final'))
    refresh(final,'none');close(values(Layout(final).master,'Results')[1][4],16)
    record('Final concentration basis no double dilution',expected=16)
    # Endpoint Trolox with mg/L, mg TE/100g: c=400, FD=2,V=.01,m=.5 =>1600.
    rows=demo_rows()
    for d in rows:d['A_end']=float(d['A_end'])-float(d['A_initial']);d['A_initial']=''
    trolox=create_experiment(root/'trolox',rows,TROLOX);refresh(trolox,'none')
    close(values(Layout(trolox).master,'Results')[1][4],1600)
    record('Trolox endpoint independent units',expected=1600,unit='mg TE/100 g')
    # Out-of-range results explicitly flagged; high R² does not suppress warning.
    rows=demo_rows()
    for d in rows:
        if d['kind']=='sample':d['A_end']=1.53
    out=create_experiment(root/'out_of_range',rows,FE);refresh(out,'none')
    assert values(Layout(out).master,'Results')[1][7]=='FUERA DE RANGO'
    record('Extrapolation QC',flag='FUERA DE RANGO')
    (root/'native_validation.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=='__main__':run(sys.argv[1])
