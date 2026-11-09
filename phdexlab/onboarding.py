"""First real launch only; health checks and construction never consume onboarding."""
import json
from .data_templates import user_data_dir
from .integration import dump

def show_on_first_use(window):
    path=user_data_dir()/'onboarding.json'
    try:seen=json.loads(path.read_text(encoding='utf-8')).get('help_seen',False)
    except (OSError,ValueError):seen=False
    if seen:return False
    window.show_help()
    path.parent.mkdir(parents=True,exist_ok=True)
    dump(path,dict(help_seen=True))
    return True
