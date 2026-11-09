"""Independent dimensional/numerical audit with desktop Excel, not a formula emulator.

Run: python tests/native_calculation_audit.py NEW_OUTPUT [OPTIONAL_REFERENCE.xlsx]
The optional reference remains local and is never bundled or uploaded.
"""
import copy,json,math,statistics,sys
from pathlib import Path
from openpyxl import load_workbook
from phdexlab.method_catalog import ALL
from phdexlab.assay_engine import columns,clean,state,engine
from phdexlab.multi_excel import write_master,sheet_name

# Dimensional oracle, explicitly separate from the production catalogue:
# umol/L -> umol/g: 1; mg/L -> mg/100g: 100;
# gallic acid umol/L -> mg/g: 170.12 g/mol / 1000; mg/L -> mg/g: 1.
FACTORS={'frap-fe-draft':1,'frap-trolox-draft':100,'abts-re':1,'abts-adapted':100,
         'cuprac-apak':1,'tpc-folin':.17012,'tpc-adapted':100,'tfc-alcl3-qe':1}


def optical(p,basis):
    p=copy.deepcopy(p);p['calibration_basis']=basis
    if p['method']=='CUPRAC':p.update(aliquot_uL=200,water_uL=900)
    p['matrix_mode']='net'
    reaction=sum(p[k] for k in ('aliquot_uL','reagent_uL','water_uL'))/p['aliquot_uL']
    axis_scale=reaction if basis=='final' else 1
    rows=[]
    def add(kind,sid,bio,tech,c=0,fd=None):
        d=dict.fromkeys(columns(p),'')
        d.update(record_id=f'R{len(rows)+1}',kind=kind,sample_id=sid,bio_id=bio,tech_id=str(tech),reading_basis='individual')
        background=(.02 if kind=='blank' else .01) if engine(p)=='inhibition' else .03 if kind in ('sample','control') else 0
        if engine(p)=='inhibition':
            a=.8 if kind=='blank' else .8*(1-(.3*c+3)/100)
            d.update(A_end=a+background,matrix_blank_delta=background)
        else:
            a=.2 if kind=='blank' else .2+.002*c+.005+background
            paired=p['reading_signal']=='paired'
            d.update(A_end=a+(.05 if paired else 0),A_initial=.05 if paired else '',matrix_blank_delta=background)
        if kind=='standard':d['concentration']=c/axis_scale
        if kind=='control':d['expected']=100/axis_scale
        if kind=='sample':d.update(dilution=fd,extract_mL=25,mass_g=.2)
        rows.append(d)
    for t in (1,2):add('blank','RB','batch',t)
    for c in (0,80,160):
        for t,error in enumerate((-1,0,1),1):add('standard',str(c),'cal',t,c+error)
        # Nominal concentrations are identical within each calibration level.
        for d in rows[-3:]:d['concentration']=c/axis_scale
    for bio,c in [('B1',120),('B2',150)]:
        for fd in (5,10):
            for t,error in enumerate((-1,0,1),1):add('sample','S',bio,t,c*5/fd+error,fd)
    for t in (1,2,3):add('control','QC','QC',t,90)
    return p,rows


def reference_assay(path):
    """Import observations/conditions, never use its cached calculation as oracle."""
    wb=load_workbook(path,data_only=True)
    try:
        p=copy.deepcopy(ALL[0]);p.update(id='frap-zenbio-aox11-audit',name='Zen-Bio AOX-11 endpoint; local verification',
            reading_signal='endpoint',reference_signal='endpoint',response='endpoint',aliquot_uL=20,
            reagent_uL=180,water_uL=0,reaction_total_uL=200,time_min=15,temperature_C=None,
            calibration_basis='before',source='https://www.zen-bio.com/pdf/cell-manuals/ZBM0119.pdf',source_updated='2020-11',
            status='Numerical verification; simulated olive observations',
            standard_range='0, 15.625, 31.25, 62.5, 125, 250, 500, 1000 umol/L before reaction; manufacturer example only',
            reagents='Kit working reagent: 14.4 mL assay buffer + 1.8 mL FeCl3 + 1.8 mL FRAP probe; proprietary kit components, not an assumed buffer composition.',
            notes='Endpoint kit procedure, 20 uL sample + 180 uL working reagent, 15 min at room temperature. Manufacturer example calibration and simulated olive observations are used only for numerical testing, never as an experimental calibration or analytically validated leaf method. No initial reading or additional sample background is supplied. Mass, volume and prior dilutions belong to the supplied simulation.')
        rows=[]
        def add(**kw):
            d=dict.fromkeys(columns(p),'');d.update(record_id=f'Z{len(rows)+1}',reading_basis='individual',**kw);rows.append(d)
        cal=wb['Calibracion_real'];xs=[];ys=[]
        for row in cal.iter_rows(min_row=6,max_row=13,values_only=True):
            c,*rest=row;readings=rest[:3];xs.append(c);ys.append(statistics.mean(readings))
            for t,a in enumerate(readings,1):
                add(kind='standard',sample_id=f'P{c}',bio_id='cal',tech_id=str(t),concentration=c,A_end=a)
                if c==0:add(kind='blank',sample_id='RB',bio_id='batch',tech_id=str(t),A_end=a)
        # Independently regress raw response; subtracting a common blank only
        # shifts the intercept and must leave interpolated concentration unchanged.
        xbar,ybar=statistics.mean(xs),statistics.mean(ys)
        slope=sum((x-xbar)*(y-ybar) for x,y in zip(xs,ys))/sum((x-xbar)**2 for x in xs)
        intercept=ybar-slope*xbar
        expected={}
        for r in wb['Olivo_simulado'].iter_rows(min_row=6,max_row=59,values_only=True):
            sid,bio,mass,volume,fd,tech,a=r[:7]
            add(kind='sample',sample_id=sid,bio_id=bio,tech_id=str(tech),A_end=a,dilution=fd,extract_mL=volume,mass_g=mass)
            expected.setdefault((sid,bio),[]).append(((a-intercept)/slope)*fd*(volume/1000)/mass)
        return dict(id='A01_FRAP',label=p['name'],protocol=p,rows=rows),expected
    finally:wb.close()


def recalc(path):
    import pythoncom,win32com.client
    pythoncom.CoInitialize();excel=None;book=None
    try:
        excel=win32com.client.DispatchEx('Excel.Application');excel.Visible=False;excel.DisplayAlerts=False
        excel.AutomationSecurity=3;excel.EnableEvents=False;excel.ScreenUpdating=False
        book=excel.Workbooks.Open(str(path.resolve()),UpdateLinks=0,ReadOnly=False)
        excel.CalculateFullRebuild();book.Save()
    finally:
        if book is not None:book.Close(False)
        if excel is not None:excel.Quit()
        pythoncom.CoUninitialize()


def run(destination,reference=None):
    out=Path(destination).resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise FileExistsError('Choose an empty audit directory')
    assays=[];expected={};blocked=[]
    def add(p,rows,wanted):
        aid=f'A{len(assays)+1:02}_{p["method"][:12]}'
        a=dict(id=aid,label=p['name'],protocol=p,rows=rows);clean(rows,p);assays.append(a);expected[aid]=wanted
    for original in ALL:
        if engine(original) in ('colorimetric','inhibition'):
            for basis in ('before','final'):
                p,rows=optical(original,basis)
                # 120 umol(or mg)/L x 5 x 0.025 L / 0.2 g = 75.
                # The second independent extraction is 150/120 as strong.
                factor=FACTORS[original['id']];assert p['report_factor']==factor
                add(p,rows,dict(biological=[75*factor,93.75*factor],recovery=90))
        elif engine(original)=='gravimetric':
            p=copy.deepcopy(original)
            if p.get('blocked_reason'):
                assert state(dict(protocol=p,rows=[]))[0]=='draft';blocked.append(p['id'])
                # These are synthetic operator-completed conditions for testing
                # the equation, never presented as the missing TAPPI standard.
                p.update(operational_confirmed=True,standard_reference='SOFTWARE TEST ONLY',endpoint_note='SYNTHETIC',temperature_C=105 if p['quantity']=='moisture' else 500,time_min=360)
            q=p['quantity'];rows=[];wanted=[]
            for b,v in enumerate((.2,.3) if q!='ash' else (.05,.06),1):
                residual=2*(1-v) if q in ('moisture','dry_matter') else 2*v
                d=dict.fromkeys(columns(p),'');d.update(record_id=str(b),kind='sample',sample_id='S',bio_id=f'B{b}',tech_id='1',tare_g=1,initial_g=3,final_g=1+residual,dry_fraction=.8);rows.append(d)
                wanted.append(100*v if q in ('moisture','ash') else 100*(1-v))
            add(p,rows,dict(biological=wanted))
            if q=='ash' and not p.get('blocked_reason'):
                p=copy.deepcopy(p);p['ash_basis']='dry';add(p,copy.deepcopy(rows),dict(biological=[6.25,7.5]))
        elif engine(original)=='ec50':
            p=copy.deepcopy(original);rows=[]
            for b,ec in [('B1',.5),('B2',.6)]:
                for dose in (.1,.4,.8):
                    d=dict.fromkeys(columns(p),'');d.update(record_id=f'D{len(rows)}',kind='sample',sample_id='S',bio_id=b,tech_id='1',dose_mg_mL=dose,time_min=45,A_end=.8*(1-(50*dose/ec)/100),matrix_blank_delta=0,plateau=True,reading_basis='individual');rows.append(d)
            d=dict.fromkeys(columns(p),'');d.update(record_id='blank',kind='blank',sample_id='RB',bio_id='batch',tech_id='1',time_min=45,A_end=.8,matrix_blank_delta=0,reading_basis='individual');rows.append(d)
            add(p,rows,dict(biological=[.5,.6]))
        else:
            p=copy.deepcopy(original);rows=[]
            for b in (1,2):
                for t,(lo,hi,m) in enumerate(((0,100,2),(100,200,3),(200,None,4.8)),1):
                    d=dict.fromkeys(columns(p),'');d.update(record_id=f'{b}-{t}',kind='sample',sample_id='S',bio_id=f'B{b}',tech_id=str(t),lower_um=lo,upper_um=hi,retained_g=m,loaded_g=10);rows.append(d)
            add(p,rows,dict(fractions=[20,30,48],recovery=98))
    path=out/'All-protocols.xlsx';write_master(path,assays,'INDEPENDENT-DIMENSIONAL-AUDIT',calculated=True);recalc(path)
    wb=load_workbook(path,data_only=True);checks=[]
    try:
        for a in assays:
            aid=a['id'];p=a['protocol'];want=expected[aid]
            actual=list(wb[sheet_name(a,'Results')].values)[1:]
            sample=[r for r in actual if r[0]=='sample']
            if 'biological' in want:
                assert len(sample)==len(want['biological'])
                for r,v in zip(sample,want['biological']):assert math.isclose(r[4],v,rel_tol=1e-10,abs_tol=1e-10),(aid,r,v)
                summary=list(wb[sheet_name(a,'Summary')].values)[1]
                assert summary[1]==2 and math.isclose(summary[2],statistics.mean(want['biological']),rel_tol=1e-10)
                assert math.isclose(summary[3],statistics.stdev(want['biological']),rel_tol=1e-10)
                if engine(p) in ('colorimetric','inhibition'):
                    control=[r for r in actual if r[0]=='control'];assert len(control)==1 and math.isclose(control[0][4],90,abs_tol=1e-9)
                    assert control[0][8]=='% recovery' and all(r[8]==p['result_unit'] for r in sample)
                    assert all(r[3]==6 for r in sample)  # 2 dilutions x 3 readings; still biological n=2.
            else:
                summary=list(wb[sheet_name(a,'Summary')].values)[1:]
                assert [round(r[2],9) for r in summary]==want['fractions']
                assert all(math.isclose(r[5],98) for r in list(wb[sheet_name(a,'MassBalance')].values)[1:])
            checks.append(dict(protocol=p['id'],basis=p['calibration_basis'],unit=p['result_unit'],expected=want,passed=True))
        errors=[(s.title,c.coordinate,c.value) for s in wb for row in s for c in row if c.data_type=='e' and c.value!='#N/A']
        assert not errors,errors
    finally:wb.close()
    reference_report=None
    if reference:
        a,oracle=reference_assay(reference);path=out/'ZenBio-Olive-verification.xlsx';write_master(path,[a],'LOCAL-USER-REFERENCE-CROSSCHECK',calculated=True);recalc(path)
        wb=load_workbook(path,data_only=True)
        try:
            actual=list(wb[sheet_name(a,'Results')].values)[1:];reference_report=[]
            for r in actual:
                expected_values=oracle[(r[1],r[2])];wanted=statistics.mean(expected_values)
                assert r[3]==6 and math.isclose(r[4],wanted,rel_tol=1e-10)
                assert math.isclose(r[5],statistics.stdev(expected_values),rel_tol=1e-10)
                reference_report.append(dict(sample=r[1],biological_unit=r[2],mean=r[4],within_unit_sd=r[5],n=r[3],unit=r[8]))
            assert all(r[1]==3 for r in list(wb[sheet_name(a,'Summary')].values)[1:])
        finally:wb.close()
    report=dict(protocol_variants=len(ALL),equation_cases=len(checks),blocked_defaults_retained=blocked,checks=checks,reference=reference_report)
    (out/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
