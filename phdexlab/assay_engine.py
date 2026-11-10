"""Assay-specific schemas and auditable Excel formulas; no Python chemistry results."""
from collections import OrderedDict
import math
from .data_entry import COLUMNS,number,normalize
from .calculations import plan as legacy_plan,groups

IDENTITY=COLUMNS[:5]
PHYSICAL=IDENTITY+['tare_g','initial_g','final_g','dry_fraction','notes','kind_label']
SIEVE=IDENTITY+['lower_um','upper_um','retained_g','loaded_g','notes','kind_label']
EC50=IDENTITY+['dose_mg_mL','time_min','A_end','matrix_blank_delta','plateau','notes','kind_label']
NUMERIC_PARAMS={'version','wavelength_nm','temperature_C','time_min','aliquot_uL','reagent_uL','water_uL','reaction_total_uL','report_factor','r2_min','cv_max_percent','recovery_min_percent','recovery_max_percent','mass_recovery_min','mass_recovery_max','default_replicates','default_dilution','default_extract_mL','default_mass_g','minimum_calibration_levels'}

def engine(p):return p.get('engine','colorimetric')
def base_columns(p):return PHYSICAL if engine(p)=='gravimetric' else SIEVE if engine(p)=='sieve' else EC50 if engine(p)=='ec50' else COLUMNS

def columns(p):
    from .reading_design import enabled,META,OPTICAL
    return base_columns(p)+META if enabled(p) and engine(p) in OPTICAL else base_columns(p)

def yes(value):return str(value).strip().lower() in ('true','1','yes','sí','si')

def required(kind,p):
    keys={'kind','sample_id','bio_id','tech_id'};e=engine(p)
    if e=='gravimetric':return keys|{'tare_g','initial_g','final_g'}|({'dry_fraction'} if p.get('quantity')=='ash' and p.get('ash_basis')=='dry' else set())
    if e=='sieve':return keys|{'lower_um','retained_g','loaded_g'}
    from .reading_design import signal,matrix_mode
    keys.add('A_end')
    if matrix_mode(p)=='legacy' or matrix_mode(p)=='net' and kind in ('sample','control'):keys.add('matrix_blank_delta')
    if e=='ec50':return keys|{'time_min'}|({'dose_mg_mL','plateau'} if kind=='sample' else set())
    if signal(p)=='paired':keys.add('A_initial')
    if kind=='standard' or kind=='control' and p.get('reading_schema')!=2:keys.add('concentration')
    if kind=='control':keys.add('expected')
    if kind=='sample':keys|={'dilution','extract_mL','mass_g'}
    return keys

def validate_protocol(p):
    from .protocols import canonical
    from .method_catalog import METHOD_NAMES
    if p.get('method') not in METHOD_NAMES:raise ValueError('Método no implementado')
    if engine(p) not in ('colorimetric','inhibition','ec50','gravimetric','sieve'):raise ValueError('Motor de cálculo desconocido')
    if not p.get('name'):raise ValueError('Nombre del protocolo obligatorio')
    canonical(p)
    from .reading_design import validate
    validate(p)
    return p

def ready_protocol(p):
    validate_protocol(p);e=engine(p)
    expected_engine={'ABTS':'inhibition','DPPH':'ec50','HUMEDAD':'gravimetric','MATERIA_SECA':'gravimetric','CENIZAS':'gravimetric','GRANULOMETRIA':'sieve'}.get(p['method'],'colorimetric')
    if e!=expected_engine:raise ValueError('Calculation engine is incompatible with the selected method')
    for key in NUMERIC_PARAMS:
        if p.get(key) is not None and not isinstance(p[key],(int,float)):raise ValueError("Revisar parámetro numérico: "+key)
    if p.get('blocked_reason'):
        if not yes(p.get('operational_confirmed')):raise ValueError(p['blocked_reason'])
        if not p.get('standard_reference') or not p.get('endpoint_note') or not p.get('temperature_C'):raise ValueError('Completar norma, temperatura y criterio final para esta adaptación')
        if p.get('quantity')=='ash' and not p.get('time_min'):raise ValueError('Registrar duración de incineración')
    if e in ('colorimetric','inhibition'):
        if e=='inhibition' and p.get('response')!='endpoint':raise ValueError('ABTS usa absorbancia final y calcula la inhibición frente al control radical')
        for key in ('aliquot_uL','reagent_uL','wavelength_nm','time_min'):
            if p.get(key) is None or not 0<float(p[key])<1e9:raise ValueError(f'Completar parámetro positivo: {key}')
        if p.get('water_uL') is None or float(p['water_uL'])<0:raise ValueError('Completar agua adicional (0 si no se añade)')
        total=sum(float(p[k]) for k in ('aliquot_uL','reagent_uL','water_uL'))
        if p.get('reaction_total_uL') is not None and abs(total-p['reaction_total_uL'])>1e-6:raise ValueError('Alícuota + reactivos + agua no coincide con el volumen final documentado')
        if p.get('calibration_basis') not in ('before','final'):raise ValueError('Base de concentración inválida')
        expected={('FRAP','Fe(II)','umol/L'):(1,'umol eq Fe(II)/g'),('FRAP','Trolox','mg/L'):(100,'mg TE/100 g'),
            ('ABTS','Trolox','umol/L'):(1,'umol TE/g'),('ABTS','Trolox','mg/L'):(100,'mg TE/100 g'),
            ('CUPRAC','Trolox','umol/L'):(1,'umol TE/g'),('TPC','Gallic acid','umol/L'):(0.17012,'mg GAE/g'),
            ('TPC','Gallic acid','mg/L'):(100,'mg GAE/100 g'),('TFC','Quercetin','mg/L'):(1,'mg QE/g'),('TFC','Rutin','mg/L'):(1,'mg RE/g')}
        key=(p['method'],p['equivalent'],p['concentration_unit'])
        if key not in expected or (p['report_factor'],p['result_unit'])!=expected[key]:raise ValueError('Patrón, unidades o factor de expresión incompatibles')
        if not 0<=p['r2_min']<=1 or not 0<p['cv_max_percent'] or not 0<=p['recovery_min_percent']<p['recovery_max_percent']:raise ValueError('Criterios QC inválidos')
    elif e=='gravimetric':
        if p.get('quantity') not in ('moisture','dry_matter','ash'):raise ValueError('Magnitud gravimétrica no soportada')
        if p.get('result_unit')!='%':raise ValueError('Gravimetric results are percentages: result_unit must be %')
        if p.get('quantity')=='ash' and p.get('ash_basis') not in ('initial','dry'):raise ValueError('Ash mass basis must be initial or dry')
    elif e=='sieve':
        if p.get('result_unit')!='% loaded mass':raise ValueError('Sieving results use % loaded mass, without renormalisation')
    elif e=='ec50':
        if p.get('result_unit')!='mg extract/mL final' or p.get('concentration_unit')!='mg/mL final':raise ValueError('DPPH EC50 doses and results must use mg extract/mL final mixture')
    return p

def clean(rows,p):
    ready_protocol(p);e=engine(p)
    if e in ('colorimetric','inhibition'):
        result=normalize(rows,p)
        if e=='inhibition' and any(d['A_end']-(d['matrix_blank_delta'] or 0)<=0 for d in result if d['kind']=='blank'):raise ValueError('El control radical corregido debe ser positivo')
        if p.get('blank_handling')!='zeroed' and not any(d['kind']=='blank' for d in result):raise ValueError('Falta blanco o control radical sin antioxidante')
        std=groups(result,{'standard'});concs={result[idx[0]-2]['concentration'] for idx in std.values()}
        minimum=int(p.get('minimum_calibration_levels',3))
        if len(concs)<minimum:raise ValueError('Se necesitan tres niveles distintos de calibración' if minimum==3 else f'Calibration requires at least {minimum} distinct levels')
        if len(std)!=len(concs):raise ValueError('Cada concentración debe tener un único nivel de patrón')
        return result
    result=[];ids=set();reps=set()
    numeric=set(PHYSICAL[5:9]+SIEVE[5:9]+['A_end','matrix_blank_delta','dose_mg_mL','time_min'])
    for row in rows:
        if not any(str(v or '').strip() for k,v in row.items() if k not in ('record_id','kind_label')):continue
        d={k:row.get(k,'') for k in columns(p)}
        if e=='ec50':
            from .reading_design import prepare_row
            d=prepare_row(d,p)
        for k in IDENTITY:
            d[k]=str(d[k] or '').strip()
            if not d[k]:raise ValueError(f'Falta {k}')
        if d['record_id'] in ids:raise ValueError('Identificador de lectura duplicado')
        ids.add(d['record_id'])
        if e=='ec50' and d['kind'] not in ('blank','sample'):raise ValueError('DPPH EC50 utiliza control radical y muestras, no calibración Trolox')
        if e!='ec50' and d['kind']!='sample':raise ValueError('En pesadas y tamizado todas las filas son muestras')
        for k in columns(p):
            if k in numeric:d[k]=number(d[k],required=k in required(d['kind'],p))
        if e=='ec50':
            d['plateau']=yes(d['plateau'])
            if d['time_min']<0 or d['kind']=='sample' and (d['dose_mg_mL'] is None or d['dose_mg_mL']<=0):raise ValueError('Dosis positiva y tiempo no negativo obligatorios')
            key=tuple(d[k] for k in IDENTITY[1:])+ (d.get('dose_mg_mL'),d['time_min'])
        elif e=='gravimetric':
            if not 0<=d['tare_g']<d['initial_g'] or not d['tare_g']<=d['final_g']<=d['initial_g']:raise ValueError('Revisar taras y masas: m0≤m2≤m1, m1>m0')
            if p.get('ash_basis')=='dry' and (d['dry_fraction'] is None or not 0<d['dry_fraction']<=1):raise ValueError('Fracción seca requerida: 0<f≤1')
            key=tuple(d[k] for k in IDENTITY[1:])
        else:
            if d['lower_um']<0 or d['upper_um'] is not None and d['upper_um']<=d['lower_um'] or d['retained_g']<0 or d['loaded_g']<=0:raise ValueError('Intervalos o masas de tamizado inválidos')
            key=tuple(d[k] for k in IDENTITY[1:])+(d['lower_um'],d['upper_um'])
        if key in reps:raise ValueError('Lectura duplicada dentro de la misma unidad')
        reps.add(key);result.append(d)
    if not result:raise ValueError('Sin lecturas')
    from .reading_design import validate_groups
    validate_groups(result,p)
    if e=='ec50':
        if any(d['A_end']-(d['matrix_blank_delta'] or 0)<=0 for d in result if d['kind']=='blank'):raise ValueError('El control radical corregido debe ser positivo')
        controls={d['time_min'] for d in result if d['kind']=='blank'}
        levels={};finals=set()
        for d in result:
            if d['kind']!='sample':continue
            if d['time_min'] not in controls:raise ValueError('Falta control radical al tiempo de una lectura DPPH')
            if d['plateau']:
                key=(d['sample_id'],d['bio_id'],d['tech_id'],d['dose_mg_mL'])
                if key in finals:raise ValueError('Marcar una sola meseta por dosis y réplica técnica')
                finals.add(key);levels.setdefault((d['sample_id'],d['bio_id']),set()).add(d['dose_mg_mL'])
        units={(d['sample_id'],d['bio_id']) for d in result if d['kind']=='sample'}
        if not units or any(len(levels.get(u,set()))<2 for u in units):raise ValueError('Cada unidad necesita mesetas confirmadas en al menos dos dosis para EC50')
        # Every entered kinetic curve needs one final plateau confirmation.
        curves={(d['sample_id'],d['bio_id'],d['tech_id'],d['dose_mg_mL']) for d in result if d['kind']=='sample'}
        if finals!=curves:raise ValueError('Hay series cinéticas sin meseta confirmada')
    if e=='sieve':
        batches={}
        for d in result:batches.setdefault((d['sample_id'],d['bio_id']),[]).append(d)
        for unit,ds in batches.items():
            if len({d['loaded_g'] for d in ds})!=1:raise ValueError('La masa cargada debe coincidir en todas las fracciones de una unidad')
            intervals=sorted({(d['lower_um'],d['upper_um'] if d['upper_um'] is not None else math.inf) for d in ds})
            if len(ds)!=len(intervals):raise ValueError('Una masa por fracción y unidad; otro tamizado utiliza otra unidad experimental')
            if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):raise ValueError('Intervalos granulométricos solapados')
    if len(result)>10000:raise ValueError('Máximo 10000 lecturas por ensayo')
    return result

def state(assay):
    try:return 'ready','',clean(assay.get('rows',[]),assay['protocol'])
    except (ValueError,TypeError,KeyError) as error:return 'draft',str(error),None

def cell_plan(rows,p):
    """Sheet roles -> formulas, raw references are resolved to names by the workbook writer."""
    e=engine(p);f={};keys=columns(p);params=list(p)
    def put(sheet,cell,formula):f.setdefault(sheet,{})[cell]='='+formula
    def raw(key,i):
        from openpyxl.utils import get_column_letter
        return f'RAW!{get_column_letter(keys.index(key)+1)}{i}'
    def par(key):return f'Parameters!$B${params.index(key)+2}'
    n=len(rows)+1
    if e in ('colorimetric','inhibition'):
        f=legacy_plan(rows,p)
        if e=='inhibition':
            for i,d in enumerate(rows,2):
                put('Processing',f'B{i}',f'RAW!G{i}-RAW!I{i}')
                put('Processing',f'C{i}',f'100*(Calibration!$J$2-B{i})/Calibration!$J$2')
            # J2 is the corrected radical control. It is never subtracted a second time.
        for i,d in enumerate(rows,2):
            if d['kind'] in ('sample','control'):put('Processing',f'D{i}',f'IF(Calibration!$J$3>0,(C{i}-Calibration!$J$4)/Calibration!$J$3,NA())')
        return f
    for i,d in enumerate(rows,2):
        put('Processing',f'A{i}',raw('record_id',i))
        if e=='gravimetric':
            t,initial,final=(raw(k,i) for k in ('tare_g','initial_g','final_g'))
            put('Processing',f'B{i}',t);put('Processing',f'C{i}',f'{initial}-{t}');put('Processing',f'D{i}',f'{final}-{t}')
            expression=f'100*(C{i}-D{i})/C{i}' if p['quantity']=='moisture' else f'100*D{i}/C{i}'
            if p['quantity']=='ash' and p.get('ash_basis')=='dry':
                put('Processing',f'F{i}',raw('dry_fraction',i));expression+=f'/F{i}'
            put('Processing',f'E{i}',expression)
        elif e=='sieve':
            put('Processing',f'B{i}',raw('retained_g',i));put('Processing',f'C{i}',raw('loaded_g',i))
            put('Processing',f'E{i}',f'100*B{i}/C{i}')
        else:
            put('Processing',f'B{i}',f"{raw('A_end',i)}-{raw('matrix_blank_delta',i)}")
            timecol=raw('time_min',2).split('!')[1][:-1]
            put('Processing',f'G{i}',f'AVERAGEIFS(Processing!$B$2:$B${n},RAW!$B$2:$B${n},"blank",RAW!${timecol}$2:${timecol}${n},{raw("time_min",i)})')
            put('Processing',f'C{i}',f'100*(1-B{i}/G{i})')
            put('Processing',f'D{i}',raw('dose_mg_mL',i) if d['kind']=='sample' else '""')
            put('Processing',f'E{i}',raw('time_min',i));put('Processing',f'F{i}',raw('plateau',i))
    result_groups=OrderedDict()
    if e=='ec50':
        curve_groups=OrderedDict()
        for i,d in enumerate(rows,2):
            if d['kind']=='sample' and d['plateau']:curve_groups.setdefault((d['sample_id'],d['bio_id'],d['dose_mg_mL']),[]).append(i)
        curves=sorted(curve_groups)
        for r,key in enumerate(curves,2):
            indices=curve_groups[key];d=rows[indices[0]-2]
            for col,k in (('A','sample_id'),('B','bio_id'),('C','dose_mg_mL')):put('DoseCurve',f'{col}{r}',raw(k,indices[0]))
            refs=','.join(f'Processing!C{i}' for i in indices)
            put('DoseCurve',f'D{r}',f'AVERAGE({refs})')
            from .reading_design import stats
            time_column=raw('time_min',2).split('!')[1][:-1]
            control=f'Processing!G{indices[0]}'
            count,sd=stats(rows,indices,p,refs,f'100/({control})')
            put('DoseCurve',f'E{r}',sd);put('DoseCurve',f'F{r}',count)
            nextrow=r+1
            if r<len(curves)+1 and curves[r-1][:2]==key[:2]:
                put('DoseCurve',f'G{r}',f'IF(AND(D{r}<=50,D{nextrow}>=50,D{nextrow}>D{r}),C{r}+(50-D{r})*(C{nextrow}-C{r})/(D{nextrow}-D{r}),"" )')
                put('DoseCurve',f'H{r}',f'IF(D{nextrow}<D{r},1,0)')
            else:put('DoseCurve',f'G{r}','""');put('DoseCurve',f'H{r}','0')
            result_groups.setdefault(('sample',key[0],key[1]),[]).append(r)
        for r,((_,sid,bio),indices) in enumerate(result_groups.items(),2):
            # A unique increasing bracket is required; no extrapolation or hidden fit.
            refs=','.join(f'DoseCurve!G{i}' for i in indices);bad=','.join(f'DoseCurve!H{i}' for i in indices)
            put('Results',f'A{r}','"sample"');put('Results',f'B{r}',f'DoseCurve!A{indices[0]}');put('Results',f'C{r}',f'DoseCurve!B{indices[0]}')
            put('Results',f'D{r}',f'MIN(DoseCurve!F{indices[0]}:F{indices[-1]})')
            put('Results',f'E{r}',f'IF(AND(COUNT({refs})>=1,SUM({bad})=0),MIN({refs}),NA())')
            put('Results',f'F{r}','NA()');put('Results',f'G{r}','NA()')
            put('Results',f'H{r}',f'IF(ISNUMBER(E{r}),"EC50 local interpolation; verify plateau","NO EC50: bracket or monotonicity")')
    else:
        for i,d in enumerate(rows,2):
            sid=d['sample_id']
            if e=='sieve':sid+=f" | {d['lower_um']:g}–{d['upper_um'] if d['upper_um'] is not None else '∞'} µm"
            result_groups.setdefault(('sample',sid,d['bio_id']),[]).append(i)
        for r,((_,sid,bio),indices) in enumerate(result_groups.items(),2):
            put('Results',f'A{r}','"sample"')
            if e=='sieve':put('Results',f'B{r}','"'+sid.replace('"','""')+'"')
            else:put('Results',f'B{r}',raw('sample_id',indices[0]))
            put('Results',f'C{r}',raw('bio_id',indices[0]));refs=','.join(f'Processing!E{i}' for i in indices)
            for col,formula in {'D':f'COUNT({refs})','E':f'AVERAGE({refs})','F':f'STDEV({refs})' if len(indices)>1 else 'NA()','G':f'IF(E{r}=0,NA(),ABS(F{r}/E{r})*100)','H':'"Operational result; review method conditions"'}.items():put('Results',f'{col}{r}',formula)
        if e=='sieve':
            batches=groups(rows,{'sample'})
            for r,((_,sid,bio),indices) in enumerate(batches.items(),2):
                put('MassBalance',f'A{r}',raw('sample_id',indices[0]));put('MassBalance',f'B{r}',raw('bio_id',indices[0]));put('MassBalance',f'C{r}',raw('loaded_g',indices[0]))
                put('MassBalance',f'D{r}','SUM('+','.join(raw('retained_g',i) for i in indices)+')');put('MassBalance',f'E{r}',f'C{r}-D{r}');put('MassBalance',f'F{r}',f'100*D{r}/C{r}')
                put('MassBalance',f'G{r}',f'IF(AND(F{r}>={par("mass_recovery_min")},F{r}<={par("mass_recovery_max")}),"OK provisional","REVIEW MASS BALANCE")')
    samples=sorted({key[1] for key in result_groups})
    for r,sid in enumerate(samples,2):
        positions=[i for i,key in enumerate(result_groups,2) if key[1]==sid];refs=','.join(f'Results!E{i}' for i in positions)
        put('Summary',f'A{r}',f'Results!B{positions[0]}');put('Summary',f'B{r}',f'COUNT({refs})')
        # Missing EC50 is not silently excluded from mean across units/SD.
        valid=f'COUNT({refs})={len(positions)}'
        put('Summary',f'C{r}',f'IF({valid},AVERAGE({refs}),NA())');put('Summary',f'D{r}',f'IF({valid},STDEV({refs}),NA())' if len(positions)>1 else 'NA()')
    return f
