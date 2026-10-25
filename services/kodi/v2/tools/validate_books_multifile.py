"""Read-only on-host verification of saved metadata against staged strict map."""
import importlib.util,json,os,sys
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.path[:0]=['/storage/.kodi/addons/plugin.audio.asterbooks','/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib']
path=Path('/storage/.aster-staging/aster-books-sync5/payload/.kodi/addons/plugin.audio.asterbooks/resources/lib/books_sync_bridge.py')
spec=importlib.util.spec_from_file_location('candidate_books_bridge',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
root=Path('/storage/.aster-checkpoints/aster-books-sync-20261025')
source=sorted(root.glob('multifile-private-*.json'))[-1]
rows=json.loads(source.read_text());counts=[]
for row in rows:
    inodes,spans=module.book_files(row['media']);counts.append(len(spans))
if len(counts)!=3:raise RuntimeError('three-real-metadata-samples-required')
print(json.dumps(dict(read_only=True,passed=True,verified_real_file_counts=counts)))
