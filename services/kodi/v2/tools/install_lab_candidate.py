"""Checkpoint/atomically install one verified HP lab candidate, never production.

System Python over SSH: old-number new-number old-sha new-sha postcheck-file.
Requires a fresh enforced native preservation check; leaves profiles/history
unchanged and refuses retries into an existing checkpoint or unpacked stage.
"""
import hashlib,json,os,re,shutil,sys,time,zipfile
from pathlib import Path,PurePosixPath
import xml.etree.ElementTree as ET

ADDON='script.astermusic.v2lab'
def require(condition,message):
    if not condition:raise RuntimeError(message)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(stage,expected):
    require(re.fullmatch('[0-9a-f]{64}',expected) is not None,'invalid-expected-hash')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('addon_id')==ADDON and manifest.get('sha256')==expected,'manifest-identity-or-hash')
    archive=manifest.get('archive')
    require(archive==ADDON+'-0.1.0.zip','unexpected-archive')
    require(digest(stage/archive)==expected,'archive-hash')
    files=manifest['files'];names=[row['path'] for row in files]
    require(1<=len(files)<=100 and len(set(names))==len(names),'manifest-file-count')
    for name in names:
        p=PurePosixPath(name)
        require(not p.is_absolute() and '..' not in p.parts and p.parts[0]==ADDON,'unsafe-member')
    with zipfile.ZipFile(stage/archive) as bundle:
        require(set(bundle.namelist())==set(names) and len(bundle.namelist())==len(names),'archive-members')
        require(sum(row.file_size for row in bundle.infolist())<=20_000_000,'archive-too-large')
        for row in files:
            require(bundle.getinfo(row['path']).file_size<=4_000_000,'member-too-large')
            data=bundle.read(row['path'])
            require(hashlib.sha256(data).hexdigest()==row['sha256'] and len(data)==row['bytes'],'member-hash')
    return manifest

def main(arguments):
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(arguments)==5,'five-arguments-required')
    old_number,new_number,old_hash,new_hash,proof_name=arguments
    require(old_number.isdecimal() and new_number.isdecimal() and int(new_number)>int(old_number)>0,'candidate-order')
    require(re.fullmatch(r'postcheck-\d+\.json',proof_name) is not None,'proof-name')
    base=Path('/storage/.aster-staging');addons=Path('/storage/.kodi/addons')
    evidence=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
    proof=json.loads((evidence/proof_name).read_text())
    age=time.time()-int(proof_name[10:-5])/1_000_000_000
    require(-10<=age<=120,'stale-native-proof')
    require(proof.get('candidate')==int(old_number) and proof.get('sha256')==old_hash,'proof-candidate')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'native-proof-'+key)
    profile=Path('/storage/.kodi/userdata/addon_data')/ADDON
    require(not (profile/'live-trial.json').exists(),'engineering-grant-active')
    old_stage=base/('aster-music-v2lab-0.1.0-candidate'+old_number)
    new_stage=base/('aster-music-v2lab-0.1.0-candidate'+new_number)
    old=verify(old_stage,old_hash);new=verify(new_stage,new_hash)
    require(all(digest(addons/row['path'])==row['sha256'] for row in old['files']),'installed-old-drift')
    root=Path('/storage/.aster-checkpoints/aster-music-expanded-trial-20261023')
    checkpoint=root/('before-candidate'+new_number);checkpoint.mkdir(mode=0o700)
    shutil.copyfile(old_stage/old['archive'],checkpoint/'recovery.zip');(checkpoint/'recovery.zip').chmod(0o600)
    require(digest(checkpoint/'recovery.zip')==old_hash,'recovery-hash')
    shutil.copyfile(evidence/proof_name,checkpoint/'native-preflight.json');(checkpoint/'native-preflight.json').chmod(0o600)
    settings=ET.parse('/storage/.kodi/userdata/guisettings.xml')
    values=sorted((node.get('id'),node.text or '') for node in settings.findall('.//setting')
        if (node.get('id') or '').startswith(('audiooutput.','videoscreen.','locale.')))
    p=checkpoint/'av-baseline.json'
    with p.open('x') as output:json.dump(dict(count=len(values),sha256=hashlib.sha256(json.dumps(values).encode()).hexdigest()),output)
    p.chmod(0o600)
    unpacked=new_stage/'unpacked';unpacked.mkdir()
    with zipfile.ZipFile(new_stage/new['archive']) as bundle:
        for row in new['files']:
            p=unpacked/row['path'];p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(bundle.read(row['path']));p.chmod(0o644)
    target=addons/ADDON;target.rename(checkpoint/'installed-addon')
    try:(unpacked/ADDON).rename(target)
    except Exception:
        (checkpoint/'installed-addon').rename(target);raise
    require(all(digest(addons/row['path'])==row['sha256'] for row in new['files']),'installed-new-drift')
    print(json.dumps(dict(candidate=int(new_number),files_verified=len(new['files']),
        previous_candidate_retained=int(old_number),profile_unchanged=True,no_kodi_restart=True)))

if __name__=='__main__':main(sys.argv[1:])
