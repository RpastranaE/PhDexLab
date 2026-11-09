"""Explicit acquisition choices. Original readings and reported means stay distinct."""
from copy import deepcopy
from .i18n import add,t

META=['reading_basis','technical_n','technical_sd']
OPTICAL={'colorimetric','inhibition','ec50'}

for pair in '''Añadir lecturas o una media|Add readings or a mean
Lecturas individuales|Individual readings
Media ya calculada|Precomputed mean
Lectura única de absorbancia|Single absorbance reading
Incremento ΔA ya medido|Already measured absorbance change ΔA
Pareja inicial/final (ΔA)|Paired initial/final readings (ΔA)
Sin corrección adicional|No additional correction
Blanco propio de muestra (neto)|Additional sample blank (net)
Blanco de reactivos medido|Measured reagent blank
Lecturas ya puestas a cero con blanco|Readings already zeroed against a reagent blank
Absorbancia · AU|Absorbance · AU
Incremento ΔA · AU|Absorbance change ΔA · AU
Absorbancia final · AU|Final absorbance · AU
Absorbancia inicial · AU|Initial absorbance · AU
Origen de la lectura|Reading basis
n técnico de la media|Technical n of the mean
DE de la respuesta · AU|Response SD · AU
Blanco propio neto · AU|Net sample blank · AU
Señal introducida|Entered signal
Entrada preferida|Preferred data entry
Lecturas por defecto|Default number of readings
Corrección de muestra|Sample background correction
Tratamiento del blanco|Reagent blank handling
Dilución previa por defecto|Default prior dilution
Volumen de extracto por defecto · mL|Default extract volume · mL
Masa de referencia por defecto · g|Default reference mass · g
No se inventan lecturas ni una DE a partir de una media. n técnico no es n biológico.|Individual readings and SD are not reconstructed from a mean. Technical n is not biological n.
Solo se requiere la lectura inicial si eliges pareja inicial/final. Cambiar de señal respecto a la referencia es una adaptación que debes documentar.|An initial reading is required only for paired initial/final input. Changing the reference signal is an adaptation that must be documented.
El blanco de reactivos se aplica una sola vez. Este campo es solo el fondo ADICIONAL de la muestra, medido sin el cromóforo y ya corregido por su propio blanco. Ejemplo: 0,620 − 0,020 de reactivos − 0,030 de fondo neto = 0,570 AU. Si no lo has medido, selecciona Sin corrección adicional.|The reagent blank is applied once. This field is only the ADDITIONAL sample background, measured without the chromophore and already corrected against its own blank. Example: 0.620 − 0.020 reagent blank − 0.030 net sample background = 0.570 AU. If you have not measured it, select No additional correction.
El número propuesto solo prepara la tabla: puedes añadir cualquier número de lecturas. No obliga a medir por triplicado.|This number only prepares the entry table: any number of readings is allowed. Triplicate measurement is not mandatory.
Elige lecturas individuales o una media por unidad biológica y condición; no ambas. Una media puede tener n y DE conocidos, pero no se crean réplicas ficticias.|Choose individual readings or one mean per biological unit and condition, never both. A mean may include known n and SD, but no artificial replicates are created.
DE técnica de la señal elegida. En modo pareja es la DE de las diferencias pareadas, no la DE final; no se deduce sin los pares originales.|Technical SD of the chosen signal. For paired input it is the SD of paired differences, not the final-reading SD; it cannot be inferred without the original pairs.
Opcional; no es el número de unidades biológicas. Si no se conoce, déjalo vacío.|Optional; this is not the number of biological units. Leave blank if unknown.
Solo para instrumentos que ya se pusieron a cero con el blanco. Se registra una sustracción adicional de cero, sin crear una medición ficticia. El control radical de ABTS/DPPH siempre sigue siendo necesario.|Only for instruments already zeroed against the blank. Additional subtraction is explicitly zero without inventing a blank measurement. ABTS/DPPH radical controls are still required.
Ya hay lecturas: para cambiar su significado, crea otro ensayo o borra explícitamente las medidas primero.|Readings already exist: create another assay or explicitly clear the measurements before changing their meaning.
Factor de dilución propuesto al preparar una muestra; es editable por muestra.|Proposed dilution factor for a sample; editable for each sample.
Volumen total de extracción propuesto. Vacío si varía entre muestras.|Proposed total extraction volume. Leave blank if it varies between samples.
Masa propuesta. Vacío si varía entre muestras; conservar la base de masa del protocolo.|Proposed reference mass. Leave blank if it varies between samples; retain the protocol mass basis.
Demo con medias ya calculadas|Demo with precomputed means
Demostración de medias · SINTÉTICO|Mean-entry demonstration · SYNTHETIC
Entrada de datos|Data entry
Señal adaptada respecto a la referencia: documentar y comprobar compatibilidad.|Signal adapted from the reference: document and check compatibility.
Número de fracciones|Number of fractions
Número de pesadas|Number of weighings
Filas por defecto|Default rows
Niveles mínimos de calibración|Minimum calibration levels
Mínimo configurable (2–100); por defecto 3. Con dos niveles el ajuste queda matemáticamente determinado y R² no demuestra linealidad. Selecciona el intervalo y número de niveles adecuados al método.|Configurable minimum (2–100); default 3. Two levels determine the line mathematically and R² does not establish linearity. Choose a suitable range and number of levels for the method.
Absorbancia única medida al tiempo definido por el protocolo. Usa varias lecturas individuales o una media ya calculada, según el origen de tus datos.|Single absorbance measured at the protocol time. Enter individual readings or a precomputed mean according to your data source.
Incremento ΔA ya obtenido por el instrumento. No es la absorbancia final: no vuelvas a restar una lectura inicial.|Absorbance change ΔA already obtained from the instrument. This is not a final absorbance: do not subtract an initial reading again.
Lectura final de cada pareja. La inicial debe corresponder a la misma reacción; alternativamente elige incremento ΔA ya medido antes de introducir datos.|Final reading of each pair. The initial reading must correspond to the same reaction; alternatively choose already measured ΔA before entering data.
Solo para patrones de calibración. Los controles de calidad usan su concentración conocida en Esperado del control, en las mismas unidades del eje de calibración.|For calibration standards only. Quality controls use their known concentration in Expected control, in the calibration-axis units.
Configurar entrada en Protocolo y condiciones|Configure entry in Protocol and conditions
Lectura individual|Individual reading'''.splitlines():add(*pair.split('|',1))

def enabled(p):return p.get('reading_schema')==2
def signal(p):
    return p.get('reading_signal','paired' if p.get('response')=='delta' else 'endpoint')
def matrix_mode(p):return p.get('matrix_mode','legacy')
def mean(row):return row.get('reading_basis')=='mean'

def configure(protocol,legacy=False):
    """Return a new design; never mutate an archived protocol."""
    p=deepcopy(protocol);p.setdefault('engine','colorimetric');p.setdefault('reading_schema',2)
    p.setdefault('default_replicates',3)
    if p.get('engine','colorimetric') in OPTICAL:
        p.setdefault('reading_signal',signal(p));p.setdefault('reference_signal',signal(p))
        p.setdefault('default_entry_mode','individual');p.setdefault('matrix_mode','net' if legacy else 'none')
        if p.get('engine','colorimetric')=='colorimetric':p.setdefault('blank_handling','measured')
        if p.get('engine','colorimetric') in ('colorimetric','inhibition'):
            p.setdefault('minimum_calibration_levels',3);p.setdefault('default_dilution',1);p.setdefault('default_extract_mL',None);p.setdefault('default_mass_g',None)
    front=['method','name','reading_signal','default_entry_mode','default_replicates','matrix_mode','blank_handling','minimum_calibration_levels','default_dilution','default_extract_mL','default_mass_g']
    return {k:p[k] for k in front if k in p}|{k:v for k,v in p.items() if k not in front}

def validate(p):
    if not enabled(p):return
    count=p.get('default_replicates',3)
    if type(count) not in (int,float) or not float(count).is_integer() or not 1<=count<=100:raise ValueError('Default readings: integer 1–100')
    if p.get('engine','colorimetric') not in OPTICAL:return
    if signal(p) not in ('endpoint','paired','delta'):raise ValueError('Unknown entered signal')
    e=p.get('engine','colorimetric')
    if e in ('inhibition','ec50') and signal(p)!='endpoint':raise ValueError('ABTS/DPPH require absorbance readings; radical control is not an initial reading')
    expected_response='delta' if signal(p) in ('paired','delta') else 'endpoint'
    if e=='colorimetric' and p.get('response')!=expected_response:raise ValueError('Entered signal and response are inconsistent')
    if p.get('default_entry_mode') not in ('individual','mean'):raise ValueError('Unknown entry mode')
    if matrix_mode(p) not in ('none','net'):raise ValueError('Unknown sample background mode')
    if p.get('blank_handling','measured') not in ('measured','zeroed'):raise ValueError('Unknown reagent blank handling')
    if e!='colorimetric' and p.get('blank_handling','measured')!='measured':raise ValueError('Radical control cannot be replaced by an instrument zero')
    minimum=p.get('minimum_calibration_levels',3)
    if type(minimum) not in (int,float) or not float(minimum).is_integer() or not 2<=minimum<=100:raise ValueError('Calibration levels: integer 2–100')
    for key in ('default_dilution','default_extract_mL','default_mass_g'):
        v=p.get(key)
        if v not in ('',None) and (type(v) not in (int,float) or not 0<v<1e12):raise ValueError('Invalid input default: '+key)

def prepare_row(row,p):
    from .data_entry import number
    d=deepcopy(row)
    if not enabled(p):return d
    basis=d.get('reading_basis') or 'individual'
    if basis not in ('individual','mean'):raise ValueError('Reading basis must be individual or mean')
    d['reading_basis']=basis
    for key in ('technical_n','technical_sd'):d[key]=number(d.get(key))
    n,sd=d['technical_n'],d['technical_sd']
    if not mean(d) and (n is not None or sd is not None):raise ValueError('n/SD of a supplied mean cannot accompany individual readings')
    if n is not None and (not n.is_integer() or not 1<=n<=1000000):raise ValueError('Technical n must be a positive integer')
    if sd is not None and (sd<0 or n==1):raise ValueError('Response SD must be nonnegative and cannot be estimated with n=1')
    if matrix_mode(p)=='none' and number(d.get('matrix_blank_delta')) not in (None,0):raise ValueError('Additional sample correction is disabled but nonzero data remain. Enable it or explicitly clear these values.')
    if p.get('engine','colorimetric')=='colorimetric' and d.get('kind')=='blank' and number(d.get('matrix_blank_delta')) not in (None,0):raise ValueError('A reagent blank does not have an additional sample background correction.')
    if p.get('blank_handling')=='zeroed' and d.get('kind')=='blank':
        end,initial=number(d.get('A_end')),number(d.get('A_initial'))
        if end is not None and (end-(initial or 0) if signal(p)=='paired' else end)!=0:raise ValueError('A nonzero reagent blank conflicts with already-zeroed input')
    return d

def validate_groups(rows,p):
    if not enabled(p):return
    groups={}
    for d in rows:
        key=unit_key(d,p)
        groups.setdefault(key,[]).append(d)
    for ds in groups.values():
        if any(mean(d) for d in ds) and len(ds)!=1:raise ValueError('Use either individual readings or one precomputed mean per unit/condition; do not mix or duplicate them.')

def unit_key(row,p):
    from .data_entry import number
    def numeric(key):
        try:return number(row.get(key))
        except (ValueError,TypeError):return str(row.get(key)).strip()
    if row.get('kind')=='blank':return ('blank',numeric('time_min') if p.get('engine')=='ec50' else None)
    return tuple(str(row.get(k) or '').strip() for k in ('kind','sample_id','bio_id'))+(numeric('dose_mg_mL'),numeric('time_min'))

def stats(rows,indices,p,refs,sd_scale='1'):
    """Excel expressions for technical n and SD, without fabricating replicates."""
    d=rows[indices[0]-2]
    if not mean(d):return f'COUNT({refs})',f'STDEV({refs})' if len(indices)>1 else 'NA()'
    from .assay_engine import columns
    from openpyxl.utils import get_column_letter
    def raw(key):return f'RAW!{get_column_letter(columns(p).index(key)+1)}{indices[0]}'
    return (raw('technical_n') if d.get('technical_n') is not None else 'NA()',
        f'{raw("technical_sd")}*ABS({sd_scale})' if d.get('technical_sd') is not None else 'NA()')

def absorbance_formula(p,row):
    return f'RAW!G{row}-RAW!H{row}' if signal(p)=='paired' else f'RAW!G{row}'

FIELDS={
 'reading_basis':('Origen de la lectura','Elige lecturas individuales o una media por unidad biológica y condición; no ambas. Una media puede tener n y DE conocidos, pero no se crean réplicas ficticias.'),
 'technical_n':('n técnico de la media','Opcional; no es el número de unidades biológicas. Si no se conoce, déjalo vacío.'),
 'technical_sd':('DE de la respuesta · AU','DE técnica de la señal elegida. En modo pareja es la DE de las diferencias pareadas, no la DE final; no se deduce sin los pares originales.'),
}
PARAMETERS={
 'minimum_calibration_levels':('Niveles mínimos de calibración','Mínimo configurable (2–100); por defecto 3. Con dos niveles el ajuste queda matemáticamente determinado y R² no demuestra linealidad. Selecciona el intervalo y número de niveles adecuados al método.'),
 'reading_signal':('Señal introducida','Solo se requiere la lectura inicial si eliges pareja inicial/final. Cambiar de señal respecto a la referencia es una adaptación que debes documentar.'),
 'default_entry_mode':('Entrada preferida',FIELDS['reading_basis'][1]),
 'default_replicates':('Lecturas por defecto','El número propuesto solo prepara la tabla: puedes añadir cualquier número de lecturas. No obliga a medir por triplicado.'),
 'matrix_mode':('Corrección de muestra','El blanco de reactivos se aplica una sola vez. Este campo es solo el fondo ADICIONAL de la muestra, medido sin el cromóforo y ya corregido por su propio blanco. Ejemplo: 0,620 − 0,020 de reactivos − 0,030 de fondo neto = 0,570 AU. Si no lo has medido, selecciona Sin corrección adicional.'),
 'blank_handling':('Tratamiento del blanco','Solo para instrumentos que ya se pusieron a cero con el blanco. Se registra una sustracción adicional de cero, sin crear una medición ficticia. El control radical de ABTS/DPPH siempre sigue siendo necesario.'),
 'default_dilution':('Dilución previa por defecto','Factor de dilución propuesto al preparar una muestra; es editable por muestra.'),
 'default_extract_mL':('Volumen de extracto por defecto · mL','Volumen total de extracción propuesto. Vacío si varía entre muestras.'),
 'default_mass_g':('Masa de referencia por defecto · g','Masa propuesta. Vacío si varía entre muestras; conservar la base de masa del protocolo.'),
}
ENUMS={
 'reading_signal':[('endpoint','Lectura única de absorbancia'),('delta','Incremento ΔA ya medido'),('paired','Pareja inicial/final (ΔA)')],
 'default_entry_mode':[('individual','Lecturas individuales'),('mean','Media ya calculada')],
 'matrix_mode':[('none','Sin corrección adicional'),('net','Blanco propio de muestra (neto)')],
 'blank_handling':[('measured','Blanco de reactivos medido'),('zeroed','Lecturas ya puestas a cero con blanco')],
}


def field_help(key,p):
    from .ui_fields import FIELDS as BASE_FIELDS
    if key=='matrix_blank_delta':return PARAMETERS['matrix_mode'][1]
    if key=='concentration' and enabled(p):return 'Solo para patrones de calibración. Los controles de calidad usan su concentración conocida en Esperado del control, en las mismas unidades del eje de calibración.'
    if key=='A_end':return {'endpoint':'Absorbancia única medida al tiempo definido por el protocolo. Usa varias lecturas individuales o una media ya calculada, según el origen de tus datos.','delta':'Incremento ΔA ya obtenido por el instrumento. No es la absorbancia final: no vuelvas a restar una lectura inicial.','paired':'Lectura final de cada pareja. La inicial debe corresponder a la misma reacción; alternativamente elige incremento ΔA ya medido antes de introducir datos.'}[signal(p)]
    return BASE_FIELDS[key][1]
