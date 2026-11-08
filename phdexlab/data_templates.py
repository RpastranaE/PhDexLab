"""Reusable input structures. Default templates never reuse experimental readings."""
import copy,json,os,uuid
from pathlib import Path
from datetime import datetime,timezone
from .assay_engine import columns,engine
from .integration import dump

MEASUREMENTS={'A_end','A_initial','matrix_blank_delta','mass_g','tare_g','initial_g','final_g','retained_g','loaded_g','dry_fraction'}

def user_data_dir():return Path(os.environ.get('PHDEXLAB_DATA_DIR',Path.home()/'Documents'/'PhDexLab'))

def make_template(name,protocol,rows,keep_readings=False):
    if not name.strip():raise ValueError('La plantilla necesita un nombre')
    clean=copy.deepcopy(rows)
    for row in clean:
        row.pop('record_id',None)
        if not keep_readings:
            for key in MEASUREMENTS & set(row):row[key]=''
            if 'plateau' in row:row['plateau']=False
    return dict(schema=1,id=uuid.uuid4().hex,name=name.strip(),method=protocol['method'],engine=engine(protocol),
        columns=list(columns(protocol)),calibration_context={key:protocol.get(key) for key in ('equivalent','concentration_unit','calibration_basis')},contains_readings=bool(keep_readings),created=datetime.now(timezone.utc).isoformat(),rows=clean)

def save_template(template,folder=None):
    folder=Path(folder) if folder is not None else user_data_dir()/'data_templates';folder.mkdir(parents=True,exist_ok=True)
    path=folder/(template['id']+'.json');dump(path,template);return path

def catalog(folder=None):
    folder=Path(folder) if folder is not None else user_data_dir()/'data_templates';result=[]
    for path in folder.glob('*.json'):
        try:
            item=json.loads(path.read_text(encoding='utf-8'))
            if item['schema']==1 and isinstance(item['rows'],list):result.append(item)
        except (KeyError,ValueError,OSError):pass
    return sorted(result,key=lambda x:x['name'].casefold())

def instantiate(template,protocol):
    if template['method']!=protocol['method'] or template['engine']!=engine(protocol) or template['columns']!=list(columns(protocol)):
        raise ValueError('La plantilla no es compatible con el método seleccionado')
    if engine(protocol) in ('colorimetric','inhibition') and template.get('calibration_context')!={key:protocol.get(key) for key in ('equivalent','concentration_unit','calibration_basis')}:
        raise ValueError('La plantilla usa otro patrón, unidad o base de concentración. Crear una plantilla compatible.')
    rows=copy.deepcopy(template['rows'])
    for row in rows:row['record_id']=uuid.uuid4().hex
    return rows
