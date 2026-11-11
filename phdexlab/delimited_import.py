"""Delimited text import: explicit numeric conventions, never evaluate formulas."""
import csv,io,re,uuid,unicodedata
from pathlib import Path
from .assay_engine import columns,engine
from .data_entry import NUMERIC
NUMERIC_RAW=NUMERIC|{'tare_g','initial_g','final_g','dry_fraction','lower_um','upper_um','retained_g','loaded_g','dose_mg_mL','time_min','technical_n','technical_sd'}

LIMIT=10000


class ImportProblem(ValueError):
    def __init__(self,code,*,row=None,field=None,value='',choices=()):
        self.code=code;self.row=row;self.field=field;self.value=value;self.choices=choices
        super().__init__(code)
    def __str__(self):return error_text(self)


def error_text(error,labels=None):
    """Short, localised feedback; row numbers refer to data, excluding headers."""
    from . import i18n
    from .ui_fields import FIELDS
    en=i18n.LANGUAGE=='en'
    if isinstance(error,UnicodeError):return 'Cannot decode the file. Try another encoding.' if en else 'No se puede leer el texto. Prueba otra codificación.'
    if isinstance(error,csv.Error):return 'Invalid quotes. Check the quote character and separator.' if en else 'Comillas incorrectas. Revisa las comillas y el separador.'
    if isinstance(error,OSError):return 'Cannot read the file. Check its location and permissions.' if en else 'No se puede leer el archivo. Revisa su ubicación y permisos.'
    if not isinstance(error,ImportProblem):return str(error)
    messages={
        'size':('El archivo supera 20 MB. Divide el archivo.','File exceeds 20 MB. Split the file.'),
        'limit':('Máximo 10 000 filas de datos. Divide el archivo.','Maximum 10,000 data rows. Split the file.'),
        'separator':('Elige un separador de un solo carácter.','Choose a single-character separator.'),
        'empty':('No hay filas de datos. Revisa encabezados y líneas omitidas.','No data rows. Check headers and skipped lines.'),
        'text':('El archivo no parece texto delimitado. Expórtalo como CSV/TXT o revisa la codificación.','File does not appear to be delimited text. Export CSV/TXT or check the encoding.'),
        'columns':('Las filas tienen distintas columnas. Revisa separador y comillas.','Rows have different column counts. Check separator and quotes.'),
        'separators':('Decimal y miles deben usar separadores distintos.','Decimal and thousands separators must differ.'),
        'grouping':('Separación de miles incorrecta. Revisa decimal y miles.','Invalid thousands grouping. Check decimal and thousands separators.'),
        'number':('Número no válido. Revisa el valor y los separadores.','Invalid number. Check the value and separators.'),
        'finite':('El número debe ser finito. Revisa el valor.','Number must be finite. Check the value.'),
        'mapping':('Asignación no válida. Vuelve a elegir la columna.','Invalid mapping. Select the source column again.'),
        'basis':('Usa individual o media. Si es el nombre del equipo, deja esta columna sin asignar.','Use individual or mean. If this is an instrument name, leave this column unassigned.'),
        'boolean':('Usa sí o no.','Use yes or no.'),
        'kind':('Tipo no reconocido.','Unknown reading type.'),
        'method_kind':('Tipo no disponible para este método.','Reading type is not available for this method.')}
    message=messages.get(error.code,('Revisa el dato.','Check the input.'))[int(en)]
    if error.code in ('kind','method_kind'):
        names={'sample':('muestra','sample'),'standard':('patrón','standard'),'blank':('blanco/control radical','blank/radical control'),'control':('control de calidad','quality control')}
        message+=(' Use: ' if en else ' Usa: ')+', '.join(names[k][int(en)] for k in error.choices)+'.'
    context=[]
    if error.row is not None:context.append(('Data row ' if en else 'Fila de datos ')+str(error.row))
    if error.field:
        label=(labels or {}).get(error.field,i18n.t(FIELDS.get(error.field,(error.field,''))[0]))
        context.append(label.replace('\n',' '))
    value=str(error.value).replace('\n',' ')[:60]
    return (' · '.join(context)+': ' if context else '')+('«'+value+'» — ' if value else '')+message


def read_text(path,encoding='auto'):
    path=Path(path)
    if path.stat().st_size>20*1024*1024:raise ImportProblem('size')
    data=path.read_bytes()
    if data.startswith((b'PK\x03\x04',b'%PDF-',b'\xd0\xcf\x11\xe0')):raise ImportProblem('text')
    if encoding=='auto':
        if data.startswith((b'\xff\xfe',b'\xfe\xff')):encoding='utf-16'
        else:
            try:data.decode('utf-8-sig');encoding='utf-8-sig'
            except UnicodeDecodeError:encoding='cp1252'
    text=data.decode(encoding)
    if '\x00' in text:raise ImportProblem('text')
    return text


def parse(text,delimiter='auto',skip=0,header=True,quote='"'):
    text='\n'.join(text.splitlines()[skip:])
    if delimiter=='auto':
        try:delimiter=csv.Sniffer().sniff(text[:16384],delimiters=',;\t|').delimiter
        except csv.Error:
            # A malformed row can defeat Sniffer. Still inspect likely delimiters
            # so inconsistent CSVs are reported instead of becoming one text column.
            first=next((line for line in text.splitlines() if line.strip()),'')
            delimiter=max(',;\t|',key=first.count) if any(c in first for c in ',;\t|') else '\t'
    if len(delimiter)!=1:raise ImportProblem('separator')
    reader=csv.reader(io.StringIO(text),delimiter=delimiter,quotechar=quote or None,quoting=csv.QUOTE_MINIMAL if quote else csv.QUOTE_NONE,strict=True)
    rows=[]
    for row in reader:
        if any(c.strip() for c in row):rows.append(row)
        if len(rows)>LIMIT+1:raise ImportProblem('limit')
    if not rows:return [],[],delimiter
    width=len(rows[0])
    for index,row in enumerate(rows[1:] if header else rows,1):
        if len(row)!=width:raise ImportProblem('columns',row=index)
    titles=rows.pop(0) if header else ['Column '+str(i+1) for i in range(width)]
    if len(rows)>LIMIT:raise ImportProblem('limit')
    return titles,rows,delimiter


def numeric(value,decimal='.',thousands=''):
    value=str(value).strip()
    if not value:return ''
    if thousands==decimal:raise ImportProblem('separators')
    if thousands:
        # Reject ambiguous/malformed grouping rather than silently altering a number.
        integer=re.split(re.escape(decimal),re.split('[eE]',value)[0])[0].lstrip('+-')
        if thousands in integer and not re.fullmatch(r'\d{1,3}(?:'+re.escape(thousands)+r'\d{3})+',integer):raise ImportProblem('grouping',value=value)
        if thousands in value[len(re.split(re.escape(decimal),value)[0])+1:]:raise ImportProblem('grouping',value=value)
        value=value.replace(thousands,'')
    pattern=r'[+-]?(?:\d+(?:'+re.escape(decimal)+r'\d*)?|'+re.escape(decimal)+r'\d+)(?:[eE][+-]?\d+)?'
    if not re.fullmatch(pattern,value):raise ImportProblem('number',value=value)
    from .data_entry import number
    result=value.replace(decimal,'.')
    try:number(result)
    except ValueError as error:raise ImportProblem('finite',value=value) from error
    return result


def normal(text):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',str(text).replace('µ','u').replace('μ','u').replace('×','x')).encode('ascii','ignore').decode().lower())


def import_fields(protocol):
    """Only fields applicable to the active protocol; archived RAW schema stays intact."""
    from .reading_design import signal,matrix_mode
    hidden={'record_id','kind_label'}
    if signal(protocol)!='paired' or engine(protocol)!='colorimetric':hidden.add('A_initial')
    if matrix_mode(protocol)=='none':hidden.add('matrix_blank_delta')
    if engine(protocol)=='gravimetric' and not (protocol.get('quantity')=='ash' and protocol.get('ash_basis')=='dry'):hidden.add('dry_fraction')
    return [key for key in columns(protocol) if key not in hidden]


def guess(titles,fields,protocol=None):
    from .ui_fields import FIELDS
    from .i18n import CATALOG
    aliases={'A_end':['absorbance','absorbancia','abs','absorbanceau','absorbanciaau'],
             'sample_id':['sample','sampleid','muestra','muestrapatron'],
             'bio_id':['unit','preparation','extraccion','unidadexperimentalextraccion'],
             'tech_id':['replicate','repeat','replica','repeticion'],
             'kind':['type','readingtype','tipodelectura'],
             'reading_basis':['readingbasis','entrymode','tipodedato','lecturasindividualesomedia'],
             'concentration':['concentration','concentracion']}
    mapping={}
    for field in fields:
        label=FIELDS.get(field,(field,''))[0]
        # "Origen de la lectura" can name an instrument/source in external files.
        # Do not infer individual/mean metadata from this ambiguous heading.
        names={normal(field)}
        if field!='reading_basis':names.update((normal(label),normal(CATALOG.get(label,label))))
        names.update(normal(v) for v in aliases.get(field,[]))
        if protocol and field in ('concentration','expected'):
            unit=protocol.get('concentration_unit','')
            labels=('Concentración del patrón','Standard concentration') if field=='concentration' else ('Esperado del control','Valor esperado del control','Expected control')
            names.update(normal(v+' '+unit) for v in labels)
        matches=[i for i,title in enumerate(titles) if normal(title) in names]
        if len(matches)==1:mapping[field]=matches[0]
    return mapping


def records(rows,mapping,protocol,existing=(),decimal='.',thousands='',default_kind='sample',default_unit='Preparation 1'):
    from .ui_fields import KIND_LABELS
    from .i18n import CATALOG
    from .assay_engine import yes
    fields=columns(protocol);result=[];used={}
    def scope(d):
        from .data_entry import number
        def value(k):
            raw=d.get(k,'')
            if k in ('dose_mg_mL','time_min','dilution') and raw not in ('',None):
                try:return number(raw)
                except ValueError:pass
            return str(raw or '').strip()
        return tuple(value(k) for k in ('kind','sample_id','bio_id','dose_mg_mL','time_min','dilution'))
    for d in existing:used.setdefault(scope(d),set()).add(str(d.get('tech_id','')))
    kinds={normal(k):k for k in KIND_LABELS}
    for k,label in KIND_LABELS.items():
        for name in (label,CATALOG.get(label,label)):kinds[normal(name)]=k
    for key,names in {
        'standard':('Patrón','Patron','Standard','Calibration standard'),
        'blank':('Blanco','Reagent blank','Control radical','Radical control','Control radical sin antioxidante','Radical control without antioxidant'),
        'control':('Control','Quality control','QC'),'sample':('Muestra','Sample')}.items():
        for name in names:kinds[normal(name)]=key
    allowed=('sample',) if engine(protocol) in ('gravimetric','sieve') else ('sample','blank') if engine(protocol)=='ec50' else tuple(KIND_LABELS)
    for i,source in enumerate(rows,1):
        row=dict.fromkeys(fields,'');row.update(record_id=uuid.uuid4().hex,kind=default_kind,bio_id=default_unit)
        for field,index in mapping.items():
            if index is None:continue
            if field not in fields or not 0<=index<len(source):raise ImportProblem('mapping',row=i,field=field)
            value=source[index].strip()
            try:
                if field in NUMERIC_RAW:value=numeric(value,decimal,thousands)
                elif field=='kind' and value:
                    value=kinds.get(normal(value),'')
                    if not value:raise ImportProblem('kind',value=source[index],choices=allowed)
                    if value not in allowed:raise ImportProblem('method_kind',value=source[index],choices=allowed)
                elif field=='reading_basis' and value:
                    value={'individual':'individual','mean':'mean','media':'mean','mediayacalculada':'mean','precomputedmean':'mean','lecturaindividual':'individual','individualreading':'individual','lecturasindividuales':'individual','individualreadings':'individual'}.get(normal(value),'')
                    if not value:raise ImportProblem('basis',value=source[index])
                elif field=='plateau' and value:
                    if normal(value) not in ('yes','si','true','1','no','false','0'):raise ImportProblem('boolean',value=value)
                    value='yes' if yes(value) else 'no'
            except ValueError as error:
                problem=error if isinstance(error,ImportProblem) else ImportProblem('number',value=source[index])
                raise ImportProblem(problem.code,row=i,field=field,value=problem.value,choices=problem.choices) from error
            row[field]=value
        if not row['kind']:row['kind']=default_kind
        if row['kind'] not in allowed:raise ImportProblem('method_kind',row=i,field='kind',value=row['kind'],choices=allowed)
        if not row.get('reading_basis') and 'reading_basis' in fields:row['reading_basis']='individual'
        if row['kind']=='sample':
            for key,param in [('dilution','default_dilution'),('extract_mL','default_extract_mL'),('mass_g','default_mass_g')]:
                if key in fields and key not in mapping and protocol.get(param) is not None:row[key]=str(protocol[param])
        if not row.get('tech_id'):
            taken=used.setdefault(scope(row),set());n=1
            while str(n) in taken:n+=1
            row['tech_id']=str(n)
        used.setdefault(scope(row),set()).add(str(row['tech_id']));result.append(row)
    return result
