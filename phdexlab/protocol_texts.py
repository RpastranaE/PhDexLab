"""Built-in scientific text and display-only translations; archived inputs stay intact."""
import json
from pathlib import Path
DATA=json.loads((Path(__file__).parent/'assets'/'protocol_locale.json').read_text(encoding='utf-8'))
TEXT_FIELDS={'name','status','notes','mass_basis','qc_policy','reagents','standard_range','blocked_reason','endpoint_note','source_updated'}
VALUE_ROLE=276

def apply_builtin(protocol):
    fields=DATA['builtins'].get(protocol.get('id'))
    if fields:protocol.update(fields);protocol['version']=2
    return protocol

def display_value(key,value):
    from . import i18n
    if key not in TEXT_FIELDS or not isinstance(value,str):return value
    english=DATA['legacy_to_en'].get(value,value)
    return english if i18n.LANGUAGE=='en' else DATA['en_to_es'].get(english,english)

def input_value(item):
    """Return the original canonical string unless the operator actually edited it."""
    stored=item.data(VALUE_ROLE)
    return stored[0] if stored is not None and item.text()==stored[1] else item.text()
