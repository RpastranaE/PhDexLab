"""Synthetic fixtures with independent expectations documented in tests; never experimental data."""
from copy import deepcopy
from .method_catalog import ALL,METHOD_NAMES
from .data_entry import COLUMNS,demo_varieties
from .assay_engine import columns,engine

def generated(p):
    e=engine(p);rows=[]
    def add(kind,sid,bio,tech,**values):
        d=dict.fromkeys(columns(p),'');d.update(record_id=f'R{len(rows)+1:05}',kind=kind,sample_id=sid,bio_id=bio,tech_id=str(tech),notes='SYNTHETIC — not experimental measurements',**values);rows.append(d)
    if e in ('colorimetric','inhibition'):
        method=p['method'];levels=(100,300,500,700,1000);centers=(400,600,800);slope=.001
        if method=='ABTS':levels=(0,3,6,9,12);centers=(3,6,9);slope=5
        if method=='CUPRAC':centers=(300,450,600)
        if method=='TPC':levels=(50,150,250,350,450);centers=(200,250,300)
        if method=='TFC':levels=(10,20,30,40,50);centers=(20,30,40);slope=.01
        def readings(c,err=0):
            if e=='inhibition':return dict(A_end=.7*(1-(2+slope*c+err)/100),A_initial='',matrix_blank_delta=0)
            return dict(A_end=round(.01+slope*c+err+(.02 if p['response']=='delta' else 0),12),A_initial=.02 if p['response']=='delta' else '',matrix_blank_delta=0)
        for t in range(1,4):add('blank','Radical control' if e=='inhibition' else 'Reagent blank','Batch',t,A_end=.7 if e=='inhibition' else .03 if p['response']=='delta' else .01,A_initial=.02 if p['response']=='delta' else '',matrix_blank_delta=0)
        for c in levels:
            for t,err in enumerate((-.001,0,.001),1):add('standard','P'+str(c),'Calibration',t,concentration=c,**readings(c,err))
        for sid,c in zip(('Variety A','Variety B','Variety C'),centers):
            for b,factor in enumerate((.95,1,1.05),1):
                for t,err in enumerate((-.001,0,.001),1):add('sample',sid,f'B{b}',t,dilution=2,extract_mL=10,mass_g=.5,**readings(c*factor,err))
        c=levels[len(levels)//2]
        for t in range(1,4):add('control','QC','QC',t,concentration=c,expected=c,**readings(c))
    elif e=='ec50':
        for time in (0,15,30):
            for t in range(1,4):add('blank','Radical control','Batch',t,time_min=time,A_end=.8,matrix_blank_delta=0,plateau=False)
        for sid,ec in zip(('Variety A','Variety B','Variety C'),(.5,1,2)):
            for b,factor in enumerate((.9,1,1.1),1):
                for dose in (.1,.25,.5,1,2,4):
                    response=min(95,50*dose/(ec*factor))
                    for t,error in enumerate((-.2,0,.2),1):
                        for time,scale in ((0,0),(15,.7),(30,1)):
                            inhibition=response*scale+error
                            add('sample',sid,f'B{b}',t,dose_mg_mL=dose,time_min=time,plateau=time==30,A_end=.8*(1-inhibition/100),matrix_blank_delta=0)
    elif e=='gravimetric':
        for sid,base in zip(('Variety A','Variety B','Variety C'),(20,30,40) if p['quantity']!='ash' else (5,6,7)):
            for b,offset in enumerate((-1,0,1),1):
                value=base+offset
                residual=10*(1-value/100) if p['quantity'] in ('moisture','dry_matter') else 10*value/100
                add('sample',sid,f'B{b}',1,tare_g=1,initial_g=11,final_g=1+residual,dry_fraction=1)
    else:
        for sid in ('Variety A','Variety B','Variety C'):
            for b,offset in enumerate((-.1,0,.1),1):
                for t,(lo,hi,mass) in enumerate(((0,100,2+offset),(100,300,5-offset),(300,None,2.8)),1):add('sample',sid,f'B{b}',t,lower_um=lo,upper_um=hi,retained_g=mass,loaded_g=10)
    return rows

def multi_demo(extended=False):
    methods=['FRAP','ABTS','CUPRAC','TPC','TFC']+(['DPPH','HUMEDAD','MATERIA_SECA','CENIZAS','GRANULOMETRIA'] if extended else [])
    assays=[]
    for i,method in enumerate(methods,1):
        p=deepcopy(next(p for p in ALL if p['method']==method))
        if method=='CUPRAC':p.update(aliquot_uL=1000,water_uL=100,name=p['name']+' · DEMO x=1000 µL',notes=p['notes']+' Alícuota sintética elegida solo para demostración; no es un valor fijado por la fuente.')
        if method=='DPPH':p['notes']+=' Meseta a 30 min únicamente en la cinética SINTÉTICA de demostración; no es un tiempo prescrito para muestras reales.'
        if method=='GRANULOMETRIA':p.update(time_min=5,sieve_amplitude='SYNTHETIC EXAMPLE — no real sieving conditions')
        assays.append(dict(id=f'A{i:02}_{method}',label=METHOD_NAMES[method],protocol=p,rows=generated(p)))
    return assays
