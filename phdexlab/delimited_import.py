"""Delimited text import: explicit numeric conventions, never evaluate formulas."""
import csv,io,re,uuid,unicodedata
from pathlib import Path
from .assay_engine import columns,engine
from .data_entry import NUMERIC
NUMERIC_RAW=NUMERIC|{'tare_g','initial_g','final_g','dry_fraction','lower_um','upper_um','retained_g','loaded_g','dose_mg_mL','time_min','technical_n','technical_sd'}

LIMIT=10000


def read_text(path,encoding='auto'):
    path=Path(path)
    if path.stat().st_size>20*1024*1024:raise ValueError('File exceeds 20 MB')
    data=path.read_bytes()
    if encoding=='auto':
        if data.startswith((b'\xff\xfe',b'\xfe\xff')):encoding='utf-16'
        else:
            try:return data.decode('utf-8-sig')
            except UnicodeDecodeError:encoding='cp1252'
    return data.decode(encoding)


def parse(text,delimiter='auto',skip=0,header=True,quote='"'):
    text='\n'.join(text.splitlines()[skip:])
    if delimiter=='auto':
        try:delimiter=csv.Sniffer().sniff(text[:16384],delimiters=',;\t|').delimiter
        except csv.Error:delimiter='\t'
    if len(delimiter)!=1:raise ValueError('Choose a single separator')
    reader=csv.reader(io.StringIO(text),delimiter=delimiter,quotechar=quote or None,quoting=csv.QUOTE_MINIMAL if quote else csv.QUOTE_NONE,strict=True)
    rows=[]
    for row in reader:
        if any(c.strip() for c in row):rows.append(row)
        if len(rows)>LIMIT+1:raise ValueError('Maximum: 10000 data rows')
    if not rows:return [],[],delimiter
    width=len(rows[0])
    if any(len(r)!=width for r in rows):raise ValueError('Rows have different column counts; check separator and quotes')
    titles=rows.pop(0) if header else ['Column '+str(i+1) for i in range(width)]
    if len(rows)>LIMIT:raise ValueError('Maximum: 10000 data rows')
    return titles,rows,delimiter


def numeric(value,decimal='.',thousands=''):
    value=str(value).strip()
    if not value:return ''
    if thousands==decimal:raise ValueError('Decimal and thousands separators must differ')
    if thousands:
        # Reject ambiguous/malformed grouping rather than silently altering a number.
        integer=re.split(re.escape(decimal),re.split('[eE]',value)[0])[0].lstrip('+-')
        if thousands in integer and not re.fullmatch(r'\d{1,3}(?:'+re.escape(thousands)+r'\d{3})+',integer):raise ValueError('Invalid thousands grouping: '+value)
        if thousands in value[len(re.split(re.escape(decimal),value)[0])+1:]:raise ValueError('Thousands separator after decimal: '+value)
        value=value.replace(thousands,'')
    pattern=r'[+-]?(?:\d+(?:'+re.escape(decimal)+r'\d*)?|'+re.escape(decimal)+r'\d+)(?:[eE][+-]?\d+)?'
    if not re.fullmatch(pattern,value):raise ValueError('Invalid number for selected separators: '+value)
    from .data_entry import number
    result=value.replace(decimal,'.');number(result);return result


def normal(text):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',str(text)).encode('ascii','ignore').decode().lower())


def guess(titles,fields):
    from .ui_fields import FIELDS
    from .i18n import t
    aliases={'A_end':['absorbance','absorbancia','abs','absorbanceau','absorbanciaau'],
             'sample_id':['sample','sampleid','muestra','muestrapatron'],
             'bio_id':['unit','preparation','extraccion','unidadexperimentalextraccion'],
             'tech_id':['replicate','repeat','replica','repeticion'],
             'kind':['type','readingtype','tipodelectura'],'concentration':['concentration','concentracion']}
    mapping={}
    for field in fields:
        names={normal(field),normal(FIELDS.get(field,(field,''))[0]),normal(t(FIELDS.get(field,(field,''))[0]))}
        names.update(normal(v) for v in aliases.get(field,[]))
        matches=[i for i,title in enumerate(titles) if normal(title) in names]
        if len(matches)==1:mapping[field]=matches[0]
    return mapping


def records(rows,mapping,protocol,existing=(),decimal='.',thousands='',default_kind='sample',default_unit='Preparation 1'):
    from .ui_fields import KIND_LABELS
    from .i18n import t
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
        for name in (label,t(label)):kinds[normal(name)]=k
    kinds.update({normal('Control radical sin antioxidante'):'blank',normal('Radical control without antioxidant'):'blank'})
    allowed=('sample',) if engine(protocol) in ('gravimetric','sieve') else ('sample','blank') if engine(protocol)=='ec50' else tuple(KIND_LABELS)
    for i,source in enumerate(rows,1):
        row=dict.fromkeys(fields,'');row.update(record_id=uuid.uuid4().hex,kind=default_kind,bio_id=default_unit)
        for field,index in mapping.items():
            if index is None:continue
            if field not in fields or not 0<=index<len(source):raise ValueError('Invalid column mapping')
            value=source[index].strip()
            try:
                if field in NUMERIC_RAW:value=numeric(value,decimal,thousands)
                elif field=='kind' and value:
                    value=kinds.get(normal(value),'')
                    if value not in allowed:raise ValueError('Unknown reading type')
                elif field=='reading_basis' and value:
                    value={'individual':'individual','mean':'mean','media':'mean','lecturasindividuales':'individual','individualreadings':'individual'}.get(normal(value),'')
                    if not value:raise ValueError('Choose individual or mean')
                elif field=='plateau' and value:
                    if normal(value) not in ('yes','si','true','1','no','false','0'):raise ValueError('Choose yes or no')
                    value='yes' if yes(value) else 'no'
            except ValueError as error:raise ValueError(f'Row {i}, {field}: {error}') from error
            row[field]=value
        if not row['kind']:row['kind']=default_kind
        if row['kind'] not in allowed:raise ValueError('Reading type does not match this method')
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
