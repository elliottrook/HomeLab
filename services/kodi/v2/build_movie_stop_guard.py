"""Immutable Search13 successor: bounded Stop acknowledgement, no UI redesign."""
import argparse,hashlib,json
from pathlib import Path
from movie_player import MEMBERS
HERE=Path(__file__).resolve().parent
OLD_SHA='fc69b8da32ddd4e86d6ff79510a3e6e737f8e325a24e99f509b43b103e0db8bf'
OLD='aster-global-search-ui13'
NEW='aster-global-search-ui14'
def digest(data):return hashlib.sha256(data).hexdigest()
def build(snapshot,output):
    snapshot,output=Path(snapshot),Path(output)
    if output.exists():raise ValueError('immutable-stop-guard-stage')
    raw=(snapshot/'manifest.json').read_bytes()
    if digest(raw)!=OLD_SHA:raise ValueError('exact-search13-required')
    manifest=json.loads(raw)
    if manifest.get('stage')!=OLD or {r['path'] for r in manifest['files']}!=MEMBERS or len(manifest['files'])!=len(MEMBERS):
        raise ValueError('search13-members')
    files={r['path']:(snapshot/r['path']).read_bytes() for r in manifest['files']}
    if any(digest(files[r['path']])!=r['sha256'] for r in manifest['files']):raise ValueError('search13-drift')
    files['movie.py']=(HERE/'movie_native/default.py').read_bytes()
    files['resources/lib/movie_player.py']=(HERE/'movie_player.py').read_bytes().replace(
        b"MOVIE_STAGE='aster-global-search-ui12'",("MOVIE_STAGE='"+NEW+"'").encode()).replace(
        b"PREVIOUS_SEARCH='01e499b94aa5f819900fa311515a95a58ead1207f9e3e272fb287590d63b282e'",
        ("PREVIOUS_SEARCH='"+OLD_SHA+"'").encode())
    files['overlay/Home.xml']=files['overlay/Home.xml'].replace((OLD+'/default.py').encode(),(NEW+'/default.py').encode())
    manifest.update(stage=NEW,previous_manifest_sha256=OLD_SHA,
        stop_acknowledgement_seconds=5,automatic_stop_retries=0,
        files=[dict(path=p,sha256=digest(d),bytes=len(d)) for p,d in sorted(files.items())])
    output.mkdir(parents=True)
    for name,data in files.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    raw=(json.dumps(manifest,indent=2)+'\n').encode();(output/'manifest.json').write_bytes(raw)
    return digest(raw)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();print(build(args.snapshot,args.output))
