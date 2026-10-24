"""Deterministic standalone read-only HP preview; no installed file overlay."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def build(output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('nonempty-preview-stage')
    files={p.relative_to(HERE/'series_preview').as_posix():p.read_bytes()
           for p in sorted((HERE/'series_preview').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for name in ('series_adapter.py','series_model.py','series_view.py'):
        files['resources/lib/'+name]=(HERE/name).read_bytes()
    records=[]
    for name,data in sorted(files.items()):
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        records.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(schema=1,kind='hp-readonly-series-preview',files=records)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(build(parser.parse_args().output))
