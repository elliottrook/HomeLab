#!/usr/bin/env python3
"""Back up the operator's lab configuration and credential custody, never media."""
import datetime,hashlib,json,os,pathlib,tarfile,tempfile
home=pathlib.Path.home();os.umask(0o077)
root=home/'lab/private-backups/operator-configs';root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
sources=[home/'.ssh',home/'lab/homelab/configs']
sources += [home/'Library/Application Support/AsterLab'/n for n in ['worker.json','guest_ed25519','guest_ed25519.pub']]
sources += list((home/'Library/LaunchAgents').glob('*homelab*.plist'))+list((home/'Library/LaunchAgents').glob('*aster*.plist'))
files=[]
for source in sources:
 if source.is_dir():files.extend(p for p in source.rglob('*') if p.is_file() and not p.is_symlink())
 elif source.is_file() and not source.is_symlink():files.append(source)
files=sorted(set(files));stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=root/(stamp+'.tar.gz');hashes={}
with tarfile.open(out,'w:gz') as t:
 for p in files:
  name=str(p.relative_to(home));hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest();t.add(p,arcname=name,recursive=False)
with tarfile.open(out) as t:
 for m in t:
  assert m.isfile() and hashlib.sha256(t.extractfile(m).read()).hexdigest()==hashes[m.name]
status={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files_verified':len(files),'archive_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'media_included':False}
(root/'status.json').write_text(json.dumps(status,indent=2));out.chmod(0o600)
print(json.dumps(status))
