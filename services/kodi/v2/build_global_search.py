"""Immutable HP search preview; no normal skin entry or player modifications."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def build(output):
    output=Path(output)
    if output.exists():raise ValueError('immutable-search-stage')
    files={p.relative_to(HERE/'search_native').as_posix():p.read_bytes()
           for p in (HERE/'search_native').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    files['resources/lib/global_search.py']=(HERE/'global_search.py').read_bytes()
    output.mkdir(parents=True)
    rows=[]
    for name,data in sorted(files.items()):
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    data=(json.dumps(dict(schema=1,kind='hp-search-preview',files=rows),indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(data)
    return hashlib.sha256(data).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(build(parser.parse_args().output))
