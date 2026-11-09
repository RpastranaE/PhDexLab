"""Locate incomplete entries without changing RAW or duplicating chemistry rules."""
from .i18n import add,t

for pair in '''Revisar entradas|Review inputs
Ensayo|Assay
Fila|Row
Campo|Field
Problema|Problem
Dato obligatorio pendiente|Required value missing
Valor numérico inválido|Invalid numeric value
Debe ser mayor que cero|Must be greater than zero
Protocolo y condiciones|Protocol and conditions
Datos del ensayo|Assay data
Se han guardado las entradas. No se ha iniciado el cálculo ni la exportación.|Inputs have been saved. Calculation and export have not started.
Corrige los campos indicados y vuelve a actualizar. Doble clic en un problema para localizarlo.|Correct the listed fields and update again. Double-click an issue to locate it.
Ir al primer problema|Go to first issue
Se muestran los primeros 200 problemas.|Showing the first 200 issues.
Calcular solo ensayos completos|Calculate complete assays only
Los ensayos incompletos se mantienen como borrador; solo se calculan los demás.|Incomplete assays remain drafts; only complete assays are calculated.
Obligatorio: completa este campo antes de actualizar y exportar.|Required: complete this field before updating and exporting.'''.splitlines():add(*pair.split('|',1))

def empty(value):return value is None or isinstance(value,str) and not value.strip()

def active(row):
    return any(not empty(v) for k,v in row.items() if k not in ('record_id','kind_label'))

def missing_fields(row,protocol):
    if not active(row):return set()
    from .assay_engine import required
    return {key for key in required(row.get('kind'),protocol) if empty(row.get(key))}

def diagnose(assays):
    from .assay_engine import ready_protocol,state,columns,PHYSICAL,SIEVE
    from .data_entry import NUMERIC,number
    result=[]
    for assay in assays:
        p=assay['protocol'];start=len(result)
        def issue(row,field,message,record_id=None):
            result.append(dict(assay_id=assay['id'],label=assay['label'],row=row,field=field,message=str(message),record_id=record_id))
        try:ready_protocol(p)
        except (ValueError,TypeError,KeyError) as error:issue(None,None,error)
        for r,row in enumerate(assay.get('rows',[]),1):
            missing=missing_fields(row,p)
            numeric=NUMERIC|set(PHYSICAL[5:9]+SIEVE[5:9]+['dose_mg_mL','time_min','technical_n','technical_sd'])
            for field in columns(p):
                if field in missing:issue(r,field,'Dato obligatorio pendiente',row.get('record_id'))
                elif field in numeric and not empty(row.get(field)):
                    try:
                        value=number(row[field])
                        positive=field in ('dilution','extract_mL','mass_g') and row.get('kind')=='sample' or field=='expected' and row.get('kind')=='control'
                        if positive and value<=0:issue(r,field,'Debe ser mayor que cero',row.get('record_id'))
                    except (ValueError,TypeError):issue(r,field,'Valor numérico inválido',row.get('record_id'))
        if len(result)==start:
            status,message,_=state(assay)
            if status!='ready':issue(None,'__data__',message)
    return result

def field_label(key):
    from .ui_fields import FIELDS
    return t(FIELDS[key][0]).replace('\n',' ') if key in FIELDS else t('Datos del ensayo' if key=='__data__' else 'Protocolo y condiciones')

def readable(message):
    """Keep the engine's reason but replace internal column keys in the display."""
    import re
    from .ui_fields import FIELDS
    message=t(str(message))
    return re.sub(r'\b('+('|'.join(sorted(FIELDS,key=len,reverse=True)))+r')\b',lambda m:field_label(m.group()),message)
