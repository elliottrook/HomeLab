"""Verify a local five-file guard package; never activates a server."""
import argparse,hashlib,json
from pathlib import Path
from build_guard import EXPECTED,IMAGE_ID
EXTRAS={'server/libs/asterBookmarkGuard.js','server/libs/asterBookmarkController.js'}
def verify(root,expected_digest):
    root=Path(root);raw=(root/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_digest:raise ValueError('guard-manifest-drift')
    manifest=json.loads(raw)
    if (manifest.get('kind')!='aster-abs-bookmark-guard.v1' or manifest.get('base_image_id')!=IMAGE_ID
        or manifest.get('deployment_authorized') is not False or manifest.get('schema_migration') is not False):raise ValueError('guard-contract')
    rows=manifest.get('files',[])
    if len(rows)!=5 or {r['path'] for r in rows}!=set(EXPECTED)|EXTRAS:raise ValueError('guard-five-targets')
    for row in rows:
        path=root/'payload'/row['path']
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256'] or row['before_sha256']!=EXPECTED.get(row['path']):raise ValueError('guard-file-drift')
    return dict(verified=True,files_verified=5,activation_performed=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('digest');args=p.parse_args();print(json.dumps(verify(args.root,args.digest)))
