#!/usr/bin/env python3
"""Raise only the local rendered-PNG cache limit after the bounds hotfix."""
import hashlib,json,os,socket,subprocess,tempfile,time
from pathlib import Path

ROOT=Path('/storage/.kodi/addons');SERIES=ROOT/'script.asterruntime/aster-series-preview24'
CACHE=SERIES/'resources/lib/series_seerr_client.py';MANIFEST=SERIES/'manifest.json'
WRAPPER=ROOT/'skin.asterhome/tools/aster_v2_series.py';FAMILY=ROOT/'script.asterruntime/family-manifest.json'
EXPECTED={
 CACHE:'afcb75b620b3e1b8c091f7fd06a488e0fd3e7fdb10c7528f0de95a56803f26c6',
 MANIFEST:'7e95b5a7229941fc835cddc7552d876c9cbf4f0f396ea62f8e65e7902cc4bbf6',
 WRAPPER:'1f592dfc80e96a75c79a87f23d3b4c09e9fdfef910a566fe754d0779f5e0afe6',
}
def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(data):return (json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
def atomic(path,data):
 fd,tmp=tempfile.mkstemp(prefix='.aster-series-cache-limit-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
  os.chmod(tmp,0o644);os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def active_players():
 request={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as client:
  client.settimeout(8);client.sendall((json.dumps(request)+'\n').encode());answer=json.loads(client.recv(4096).decode())
 if answer.get('result')!=[]:raise RuntimeError('active player; repair refused')
def main():
 host=socket.gethostname()
 if host not in ('AsterTV-Bedroom','AsterTV-Family'):raise RuntimeError('target refused')
 active_players();originals={path:path.read_bytes() for path in set(EXPECTED)|{FAMILY}}
 for path,expected in EXPECTED.items():
  if sha(originals[path])!=expected:raise RuntimeError('baseline drift: '+str(path))
 cache=originals[CACHE].decode();old='0 < target.stat().st_size <= 5 * 1024 * 1024';new='0 < target.stat().st_size <= 32 * 1024 * 1024'
 if cache.count(old)!=2:raise RuntimeError('cache-limit callsite drift')
 cache_data=cache.replace(old,new).encode();manifest=json.loads(originals[MANIFEST]);row=next(r for r in manifest['files'] if r['path']=='resources/lib/series_seerr_client.py');row.update(bytes=len(cache_data),sha256=sha(cache_data));manifest_data=encoded(manifest)
 wrapper=originals[WRAPPER].decode()
 if wrapper.count(EXPECTED[MANIFEST])!=1:raise RuntimeError('wrapper pin drift')
 wrapper_data=wrapper.replace(EXPECTED[MANIFEST],sha(manifest_data)).encode();family=json.loads(originals[FAMILY]);family['components']['aster-series-preview24']={'files':9,'manifest_sha256':sha(manifest_data)};family['skin']['tools/aster_v2_series.py']=sha(wrapper_data);family_data=encoded(family);changed={CACHE:cache_data,MANIFEST:manifest_data,WRAPPER:wrapper_data,FAMILY:family_data}
 checkpoint=Path('/storage/.aster-checkpoints')/('astertv-v3-series-cache-limit-'+host+'-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime()));checkpoint.mkdir(mode=0o700)
 for path in changed:saved=checkpoint/str(path.relative_to(ROOT)).replace('/','__');saved.write_bytes(originals[path]);saved.chmod(0o600)
 try:subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
 except Exception:
  subprocess.run(['systemctl','reset-failed','kodi'],check=False,timeout=10);subprocess.run(['systemctl','start','kodi'],check=False,timeout=30);raise
 try:
  for path,data in changed.items():atomic(path,data)
  for path,data in changed.items():
   if sha(path.read_bytes())!=sha(data):raise RuntimeError('post-write mismatch: '+str(path))
 except Exception:
  for path,data in originals.items():atomic(path,data)
  Path('/storage/.aster-recovery-required').write_text(str(checkpoint)+'\n');raise
 finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
 print(json.dumps({'installed':True,'host':host,'checkpoint':str(checkpoint),'manifest_sha256':sha(manifest_data),'cache_sha256':sha(cache_data)},sort_keys=True))
if __name__=='__main__':main()
