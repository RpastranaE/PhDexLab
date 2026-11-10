"""User libraries. Removal never visits experiment folders or protocol snapshots."""
import copy,json
from pathlib import Path
from .data_templates import user_data_dir
from .integration import dump,file_hash
from .protocols import digest

def folder_for(kind,folder=None):
    if kind not in ('data','protocol'):raise ValueError('Unknown library')
    return Path(folder) if folder is not None else user_data_dir()/('data_templates' if kind=='data' else 'protocol_variants')

def preference_path():return user_data_dir()/'_internal/library.json'

def save_hidden(hidden):
    path=preference_path();path.parent.mkdir(parents=True,exist_ok=True)
    dump(path,dict(hidden_protocols=sorted(hidden)))

def hidden_protocols():
    try:return set(json.loads(preference_path().read_text(encoding='utf-8'))['hidden_protocols'])
    except (OSError,ValueError,KeyError,TypeError):return set()

def entries(kind,folder=None,include_hidden=False):
    root=folder_for(kind,folder);items=[]
    if kind=='protocol':
        from .method_catalog import ALL
        hidden=hidden_protocols()
        for p in ALL:
            key='builtin:'+digest(p)
            if include_hidden or key not in hidden:items.append(dict(key=key,payload=copy.deepcopy(p),included=True,hidden=key in hidden))
    for path in sorted(root.glob('*.json')):
        # Never follow a library symlink into an experiment or another directory.
        if path.resolve().parent!=root.resolve() or path.is_symlink():continue
        try:
            payload=json.loads(path.read_text(encoding='utf-8'))
            if kind=='protocol':
                from .assay_engine import validate_protocol
                validate_protocol(payload)
            elif payload['schema']!=1 or not isinstance(payload['rows'],list):continue
            if not payload['name'] or not payload['method']:continue
            items.append(dict(key=path.name,payload=payload,included=False,hidden=False,sha256=file_hash(path)))
        except (ValueError,KeyError,TypeError,OSError):continue
    return items

def remove(kind,entry,folder=None):
    current=next((x for x in entries(kind,folder,True) if x['key']==entry['key']),None)
    if current is None:raise ValueError('La entrada ya no existe. Actualiza la biblioteca.')
    if current['included']:
        hidden=hidden_protocols();hidden.add(current['key'])
        save_hidden(hidden)
    else:
        if current['sha256']!=entry.get('sha256'):raise ValueError('La entrada ha cambiado. Actualiza la biblioteca antes de eliminarla.')
        path=folder_for(kind,folder)/current['key']
        if path.is_symlink() or path.resolve().parent!=folder_for(kind,folder).resolve():raise ValueError('Invalid library path')
        path.unlink()

def restore(entry):
    if not entry.get('included'):raise ValueError('Only included protocols can be restored')
    hidden=hidden_protocols();hidden.discard(entry['key'])
    save_hidden(hidden)

def variants(folder=None):return [x['payload'] for x in entries('protocol',folder)]
