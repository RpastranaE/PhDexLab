"""Protocol catalogue from user-supplied drafts plus one explicitly cited published TFC base."""
from copy import deepcopy
from .protocols import FE,TROLOX

URL='Local protocol reference: '
def make(method,id,name,engine='colorimetric',**changes):
    p=deepcopy(FE);p.update(method=method,id=id,name=name,engine=engine,response='endpoint',temperature_C=None,
        standard_range='Seleccionar y verificar el intervalo lineal',notes='Transferencia a la matriz pendiente de validación.',
        source_updated='2026-11-08',reaction_total_uL=None,blocked_reason='',operational_confirmed=False)
    p.update(changes);return p

ABTS=make('ABTS','abts-re','ABTS · Re · 6 min','inhibition',equivalent='Trolox',concentration_unit='umol/L',
    result_unit='umol TE/g',report_factor=1,calibration_basis='final',wavelength_nm=734,time_min=6,temperature_C=30,
    aliquot_uL=10,reagent_uL=1000,water_uL=0,reaction_total_uL=1010,
    source=URL+'personal-reference-met-01',standard_range='0–15 µmol/L finales según fuente; verificar linealidad',
    reagents='ABTS 7 mM; persulfato 2,45 mM final; 12–16 h oscuridad; diluir con etanol hasta A734=0,70±0,02.',
    notes='Punto de lectura a 6 min de la serie 1–6 min; confirmar cinética. Tipo blank = control radical con disolvente, a idéntico tiempo. Respuesta = 100*(A_control - A_corregida)/A_control. No restar de nuevo el control como blanco.')
ABTS_ADAPT=deepcopy(ABTS);ABTS_ADAPT.update(id='abts-adapted',name='ABTS · adaptado · 30 min',
    time_min=30,temperature_C=25,aliquot_uL=200,reagent_uL=3000,reaction_total_uL=3200,calibration_basis='before',
    concentration_unit='mg/L',report_factor=100,result_unit='mg TE/100 g',source=URL+'personal-reference-met-02',
    standard_range='No especificado; definir experimentalmente',notes=ABTS['notes']+' Variante publicada 30 min, 25±2 °C, vórtex ~5 s. Preparación del radical complementaria, por confirmar.')
CUPRAC=make('CUPRAC','cuprac-apak','CUPRAC · normal · 60 min',equivalent='Trolox',concentration_unit='umol/L',
    result_unit='umol TE/g',wavelength_nm=450,time_min=60,aliquot_uL=None,reagent_uL=3000,water_uL=None,reaction_total_uL=4100,
    source=URL+'personal-reference-met-03',
    reagents='1 mL CuCl2 10 mM + 1 mL neocuproína 7,5 mM + 1 mL acetato amónico 1 M pH 7; x mL muestra + (1,10−x) mL agua.',
    notes='Introducir alícuota x en µL y agua para completar 4100 µL. 0<x≤1100 µL. Fuente: procedimiento 60 min; resumen 30 min, discrepancia conservada. No se adopta hidrólisis ni calentamiento por defecto.')
TPC=make('TPC','tpc-folin','TPC · Folin–Ciocalteu · 120 min',equivalent='Gallic acid',concentration_unit='umol/L',
    report_factor=0.17012,result_unit='mg GAE/g',wavelength_nm=765,time_min=120,temperature_C=20,
    aliquot_uL=100,reagent_uL=1000,water_uL=0,reaction_total_uL=1100,
    source=URL+'personal-reference-met-04',standard_range='50–2500 µmol/L antes de reacción; seleccionar tramo lineal',
    reagents='100 µL muestra + 200 µL Folin 10% v/v + 800 µL Na2CO3 700 mM. Folin ANTES del álcali. Lectura de 200 µL transferidos a placa.',
    notes='Conversión de µmol/L a mg/L: 170,12/1000 para ácido gálico. La transferencia a placa no añade dilución. Folin responde a otros reductores; TPC operacional.')
TPC_ADAPT=deepcopy(TPC);TPC_ADAPT.update(id='tpc-adapted',name='TPC · adaptado · 30 min',
    time_min=30,temperature_C=None,aliquot_uL=200,reagent_uL=600,water_uL=500,reaction_total_uL=1300,
    concentration_unit='mg/L',report_factor=100,result_unit='mg GAE/100 g',source=URL+'personal-reference-met-05',
    standard_range='No especificado; definir experimentalmente',
    reagents='200 µL extracto + 500 µL agua + 500 µL Na2CO3 7,5%; esperar 5 min; añadir 100 µL Folin 2 N. 30 min oscuridad.',
    notes='Orden de adición distinto de TPC base. Base m/v de Na2CO3 por confirmar. No intercambiar variantes. Concentración antes de reacción en mg/L.')
TFC=make('TFC','tfc-alcl3-qe','TFC · AlCl₃ · quercetina · 30 min',equivalent='Quercetin',concentration_unit='mg/L',
    report_factor=1,result_unit='mg QE/g',wavelength_nm=415,time_min=30,aliquot_uL=500,reagent_uL=1700,water_uL=2800,reaction_total_uL=5000,
    source='https://doi.org/10.1038/s41598-023-42418-1',
    reagents='0,5 mL muestra + 1,5 mL etanol 95% + 0,1 mL AlCl3 10% + 0,1 mL acetato potásico 1 M + 2,8 mL agua; 30 min; 415 nm.',
    notes='Base publicada en Scientific Reports 2023, siguiendo Chang et al. 2002 (doi:10.38212/2224-6614.2748). Quercetina; resultado mg QE/g. Respuesta selectiva AlCl3, no cuantifica todas las clases de flavonoides. Preparación de extracción independiente. Temperatura numérica no fijada; registrar real. No es norma ni método validado para olivo.')
DPPH=make('DPPH','dpph-bw','DPPH · cinética y EC50','ec50',response='inhibition',equivalent='Sample mass',concentration_unit='mg/mL final',
    report_factor=1,result_unit='mg extract/mL final',mass_basis='extracto seco; dosis en mezcla final',wavelength_nm=515,time_min=None,aliquot_uL=100,reagent_uL=3900,water_uL=0,reaction_total_uL=4000,
    source=URL+'personal-reference-met-06',
    reagents='DPPH 60 µmol/L en metanol; 0,10 mL muestra + 3,90 mL reactivo; control con metanol.',
    notes='Registrar cinética 0, 1 y cada 15 min hasta meseta. Marcar meseta confirmada por el operador. EC50 por interpolación lineal local entre niveles que encierran 50%; decisión informática explícita, sin extrapolar. Dosis en mg de extracto seco/mL FINAL (alícuota /40). No se asignan 30 min ni una molaridad del extracto.')

def physical(method,id,name,quantity,source,**kw):
    return make(method,id,name,'gravimetric',quantity=quantity,source=URL+source,equivalent='Not applicable',
        concentration_unit='Not applicable',result_unit='%',report_factor=1,aliquot_uL=None,reagent_uL=None,water_uL=None,
        wavelength_nm=None,time_min=None,temperature_C=None,mass_basis='masa inicial ensayada; registrar estado',ash_basis='initial',endpoint_note='',**kw)
MOISTURE=physical('HUMEDAD','moisture-oven','Humedad · estufa 105 °C','moisture','personal-reference-met-07')
MOISTURE.update(temperature_C=105,notes='10 g aproximados; duplicados. Hasta masa constante; documentar ciclos y criterio de constancia. No se inventa una duración fija.')
DRY=physical('MATERIA_SECA','dry-matter','Materia seca · 105 °C','dry_matter','personal-reference-met-08')
DRY.update(temperature_C=105,notes='Triplicados; hasta masa constante. MS y humedad son complementarias si proceden de la misma alícuota. No se normalizan otros ensayos automáticamente.')
ASH=physical('CENIZAS','ash-500','Cenizas · 500 °C · 6 h','ash','personal-reference-met-09')
ASH.update(temperature_C=500,time_min=360,notes='Triplicados. Masa de ensayo y rampa por fijar. Base inicial o seca explícita; no corregir humedad dos veces.')
MOISTURE_ADAPT=deepcopy(MOISTURE);MOISTURE_ADAPT.update(id='moisture-adapted',name='Humedad · adaptado · TAPPI pendiente',temperature_C=None,
    source=URL+'personal-reference-met-10',blocked_reason='Falta identificar norma TAPPI y condiciones. El presecado 40 °C/48 h NO es el ensayo de humedad.',standard_reference='')
ASH_ADAPT=deepcopy(ASH);ASH_ADAPT.update(id='ash-adapted',name='Cenizas · adaptado · TAPPI pendiente',temperature_C=None,time_min=None,
    source=URL+'personal-reference-met-11',blocked_reason='Faltan norma TAPPI, temperatura, duración y punto final; no heredar 500 °C/6 h como publicados.',standard_reference='')
SIEVE=make('GRANULOMETRIA','sieve-mass','Granulometría · distribución másica','sieve',
    equivalent='Not applicable',concentration_unit='Not applicable',result_unit='% loaded mass',wavelength_nm=None,
    aliquot_uL=None,reagent_uL=None,water_uL=None,time_min=None,sieve_amplitude='',temperature_C=None,
    source=URL+'personal-reference-met-12',mass_basis='masa cargada al tamizado',mass_recovery_min=98,mass_recovery_max=102,
    notes='Adaptación de distribución másica: introducir aberturas reales y fracción pasante–retenida. Cierre respecto a masa cargada; no normalizar al 100%. Fijar tiempo y amplitud. Umbrales de recuperación ilustrativos, editables.')
EXTRA=[ABTS,ABTS_ADAPT,CUPRAC,DPPH,TPC,TPC_ADAPT,TFC,MOISTURE,DRY,ASH,MOISTURE_ADAPT,ASH_ADAPT,SIEVE]
ALL=[deepcopy(FE),deepcopy(TROLOX)]+EXTRA
METHOD_NAMES={'FRAP':'FRAP','ABTS':'ABTS','CUPRAC':'CUPRAC','DPPH':'DPPH / EC50','TPC':'TPC · Folin','TFC':'TFC · AlCl₃','HUMEDAD':'Humedad','MATERIA_SECA':'Materia seca','CENIZAS':'Cenizas','GRANULOMETRIA':'Granulometría'}
# Source edit dates remain separate from this application's retrieval date.
for _protocol in EXTRA:
    _protocol['source_updated']=('2023 (artículo)' if _protocol['method']=='TFC' else '2026-11-02' if 'adapted' in _protocol['id'] else '2026-10-28' if _protocol['method'] in ('ABTS','CUPRAC','DPPH') else '2026-10-29')
    _protocol['source_retrieved']='2026-11-08'
# ALL holds the same EXTRA objects, and independent copies of the two existing FRAP variants.
