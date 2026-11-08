"""Content-addressed exported artifacts. Every reuse verifies the actual file bytes."""
import shutil
import re
from .paths import Layout
from .integration import file_hash

def store(folder,files):
    l=Layout(folder);cache=l.meta/'export_cache';cache.mkdir(exist_ok=True);entries={}
    for name in files:
        source=l.root/name;sha=file_hash(source);destination=cache/(sha+source.suffix)
        if not destination.exists() or file_hash(destination)!=sha:shutil.copy2(source,destination)
        entries[str(name)]=sha
    return entries

def restore(folder,entries):
    if not entries:return False
    l=Layout(folder);sources=[]
    for name,sha in entries.items():
        destination=(l.root/name).resolve()
        if not destination.is_relative_to(l.root) or not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):return False
        source=l.meta/'export_cache'/(sha+destination.suffix)
        if not source.is_file() or file_hash(source)!=sha:return False
        sources.append((source,destination))
    for source,destination in sources:
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    return True
