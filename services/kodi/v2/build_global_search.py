"""Immutable HP search preview; no normal skin entry or player modifications."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def build(output,details=False):
    output=Path(output)
    if output.exists():raise ValueError('immutable-search-stage')
    files={p.relative_to(HERE/'search_native').as_posix():p.read_bytes()
           for p in (HERE/'search_native').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if not details:files.pop('overlay/custom_1128_searchdetails.xml',None)
    files['resources/lib/global_search.py']=(HERE/'global_search.py').read_bytes()
    if details:
        from build_series_integration import dispatcher as series_dispatcher
        from search_integration import dispatcher
        original=(HERE.parent/'skin.asterhome/tools/select_dispatch.py').read_text()
        files['overlay/select_dispatch.py']=dispatcher(series_dispatcher(original).encode())
        files['resources/lib/search_details.py']=(HERE/'search_details.py').read_bytes()
    output.mkdir(parents=True)
    rows=[]
    for name,data in sorted(files.items()):
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(schema=1,kind='hp-search-details' if details else 'hp-search-preview',files=rows)
    if details:
        from search_integration import BEFORE
        manifest.update(previous_manifest_sha256='97439284ffadb61a6375853569cabdc2f085c5f41b8d3a51fbdabdf66136b6bc',
                        dispatcher_before_sha256=BEFORE)
    data=(json.dumps(manifest,indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(data)
    return hashlib.sha256(data).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--details',action='store_true')
    args=parser.parse_args();print(build(args.output,args.details))
