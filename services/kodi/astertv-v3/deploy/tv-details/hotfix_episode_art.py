#!/usr/bin/env python3
"""Bind episode stills and remove the full-height season backplate."""
import hashlib,json,os,socket,subprocess,tempfile,time
from pathlib import Path
ROOT=Path('/storage/.kodi/addons');HERE=Path(__file__).resolve().parent;SERIES=ROOT/'script.asterruntime/aster-series-preview24';XML=SERIES/'resources/skins/Default/1080i/SeriesPreview.xml';MANIFEST=SERIES/'manifest.json';WRAPPER=ROOT/'skin.asterhome/tools/aster_v2_series.py';FAMILY=ROOT/'script.asterruntime/family-manifest.json'
EXPECTED={XML:'61502e614b786c513cd110cde5a399b6e842e695ca471533365e8e983816074a',MANIFEST:'bd4bffc5d94064142337243f2e3a21584c00e05059ccd7753aeabbdf6769207a',WRAPPER:'495e2f66345bf64589bdb0de0c15d943be6576f5f9f3f69afa1029c5a1fc6c3e'}
def sha(b):return hashlib.sha256(b).hexdigest()
def atomic(p,b):
 fd,t=tempfile.mkstemp(prefix='.aster-v3-episode-art-',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.chmod(t,0o644);os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def main():
 host=socket.gethostname()
 if host not in ('AsterTV-Bedroom','AsterTV-Family'):raise RuntimeError('target refused')
 old={p:p.read_bytes() for p in set(EXPECTED)|{FAMILY}}
 for p,h in EXPECTED.items():
  if sha(old[p])!=h:raise RuntimeError('baseline drift: '+str(p))
 xml=(HERE/'aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml').read_bytes()
 if xml.count(b'ListItem.Property(Still)')!=2 or b'<height>720</height>' in xml:raise RuntimeError('episode-art candidate invalid')
 manifest=json.loads(old[MANIFEST]);row=next(r for r in manifest['files'] if r['path']=='resources/skins/Default/1080i/SeriesPreview.xml');row.update(bytes=len(xml),sha256=sha(xml));manifest_data=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
 wrapper=old[WRAPPER].decode()
 if wrapper.count(EXPECTED[MANIFEST])!=1:raise RuntimeError('wrapper pin drift')
 wrapper=wrapper.replace(EXPECTED[MANIFEST],sha(manifest_data)).encode();family=json.loads(old[FAMILY]);family['components']['aster-series-preview24']={'files':9,'manifest_sha256':sha(manifest_data)};family['skin']['tools/aster_v2_series.py']=sha(wrapper);family_data=(json.dumps(family,indent=2,sort_keys=True)+'\n').encode();changed={XML:xml,MANIFEST:manifest_data,WRAPPER:wrapper,FAMILY:family_data}
 cp=Path('/storage/.aster-checkpoints')/('astertv-v3-episode-art-'+host+'-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime()));cp.mkdir(mode=0o700)
 for p in changed:(cp/str(p.relative_to(ROOT)).replace('/','__')).write_bytes(old[p])
 subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
 try:
  for p,b in changed.items():atomic(p,b)
  for p,b in changed.items():
   if sha(p.read_bytes())!=sha(b):raise RuntimeError('post-write mismatch')
 except Exception:
  for p,b in old.items():atomic(p,b)
  raise
 finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
 print(json.dumps({'installed':True,'host':host,'checkpoint':str(cp),'manifest_sha256':sha(manifest_data)},sort_keys=True))
if __name__=='__main__':main()
