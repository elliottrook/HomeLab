"""Verify five staged HP preview files and their isolated restore, no install."""
import hashlib,json,os,re,shutil,sys,time
from pathlib import Path

def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main(args):
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(args)==3,'three-arguments-required')
    name,expected,proof=args
    require(re.fullmatch(r'aster-series-preview[1-9][0-9]*',name) is not None,'invalid-stage')
    require(re.fullmatch('[0-9a-f]{64}',expected) is not None,'invalid-hash')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof) is not None,'invalid-proof')
    stage=Path('/storage/.aster-staging')/name
    require(digest(stage/'manifest.json')==expected,'manifest-hash')
    manifest=json.loads((stage/'manifest.json').read_text())
    names={'default.py','resources/lib/series_adapter.py','resources/lib/series_model.py','resources/lib/series_view.py',
        'resources/skins/Default/1080i/SeriesPreview.xml'}
    require(manifest.get('schema')==1 and manifest.get('kind')=='hp-readonly-series-preview','manifest-kind')
    require(len(manifest['files'])==5 and {r['path'] for r in manifest['files']}==names,'exact-preview-members')
    for row in manifest['files']:
        path=stage/row['path'];require(not path.is_symlink() and path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],'member-hash')
    require(digest(Path('/storage/.kodi/addons/plugin.video.asterhome/library.py'))==
        'f1e0bf2192d99936529a6092ad80d6cd4483d95903f5e87d15a4ff4afc48d0a0','accepted-up-next-source')
    evidence=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof
    native=json.loads(evidence.read_text());age=time.time()-int(proof[10:-5])/1_000_000_000
    require(-10<=age<=120 and native.get('candidate')==64,'fresh-music64-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(native.get(key) is True,'idle-proof-'+key)
    checkpoint=Path('/storage/.aster-checkpoints/aster-series-preview-20261024')/name
    checkpoint.mkdir(mode=0o700,parents=True)
    require(not any(checkpoint.iterdir()),'checkpoint-already-used')
    shutil.copytree(stage,checkpoint/'isolated-restore')
    require(digest(checkpoint/'isolated-restore/manifest.json')==expected,'restored-manifest')
    for row in manifest['files']:require(digest(checkpoint/'isolated-restore'/row['path'])==row['sha256'],'restored-member')
    shutil.copyfile(evidence,checkpoint/'native-preflight.json')
    for path in checkpoint.rglob('*'):path.chmod(0o700 if path.is_dir() else 0o600)
    print(json.dumps(dict(stage=name,files_verified=5,isolated_restore_verified=True,installed_files_changed=0)))

if __name__=='__main__':main(sys.argv[1:])
