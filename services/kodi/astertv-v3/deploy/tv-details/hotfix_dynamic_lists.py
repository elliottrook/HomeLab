#!/usr/bin/env python3
"""Remove TV fixture content and enable the v3 dynamic-control dispatcher."""
from __future__ import annotations

import hashlib, json, os, socket, subprocess, tempfile, time
from pathlib import Path

ROOT=Path('/storage/.kodi/addons')
HERE=Path(__file__).resolve().parent
SERIES=ROOT/'script.asterruntime/aster-series-preview24'
XML=SERIES/'resources/skins/Default/1080i/SeriesPreview.xml'
EXT=SERIES/'v3_series_extension.py'
MANIFEST=SERIES/'manifest.json'
WRAPPER=ROOT/'skin.asterhome/tools/aster_v2_series.py'
FAMILY=ROOT/'script.asterruntime/family-manifest.json'
EXPECTED={
 XML:'d34584c3107d176e855f96a858279b1605263ceefd9bcdf95652af3f623cfc9e',
 EXT:'c4dcd8fc73bb694dbc150e8e05a3c6aec86f828fdbe97a8b23523d9c70e30ef4',
 MANIFEST:'644ef0a3aa5f4d720c65091cf454f23f3be2624e5a173b5939b529c5f381e366',
 WRAPPER:'5cd69c0f62d666eba47cb6cc1094f1ea3091d1952e800dd2645dc014c8ceafb0',
}

def sha(data): return hashlib.sha256(data).hexdigest()
def encoded(data): return (json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
def atomic(path,data):
 fd,tmp=tempfile.mkstemp(prefix='.aster-v3-lists-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as out: out.write(data);out.flush();os.fsync(out.fileno())
  os.chmod(tmp,0o644);os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)

def main():
 host=socket.gethostname()
 if host not in ('AsterTV-Bedroom','AsterTV-Family'):raise RuntimeError('target refused')
 originals={p:p.read_bytes() for p in set(EXPECTED)|{FAMILY}}
 for path,expected in EXPECTED.items():
  if sha(originals[path])!=expected:raise RuntimeError('baseline drift: '+str(path))
 xml=(HERE/'aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml').read_bytes()
 extension=(HERE/'aster-series-preview24/v3_series_extension.py').read_bytes()
 if b'Aurora Station' in xml or b'The Signal Above' in xml:raise RuntimeError('fixture data remains')
 manifest=json.loads(originals[MANIFEST]);rows={r['path']:r for r in manifest['files']}
 rows['resources/skins/Default/1080i/SeriesPreview.xml'].update(bytes=len(xml),sha256=sha(xml))
 rows['v3_series_extension.py'].update(bytes=len(extension),sha256=sha(extension))
 manifest['files']=[rows[k] for k in sorted(rows)];manifest_data=encoded(manifest)
 wrapper=originals[WRAPPER].decode()
 old=EXPECTED[MANIFEST]
 if wrapper.count(old)!=1:raise RuntimeError('wrapper pin drift')
 wrapper=wrapper.replace(old,sha(manifest_data)).encode()
 family=json.loads(originals[FAMILY]);family['components']['aster-series-preview24']={'files':9,'manifest_sha256':sha(manifest_data)}
 family['skin']['tools/aster_v2_series.py']=sha(wrapper);family_data=encoded(family)
 changed={XML:xml,EXT:extension,MANIFEST:manifest_data,WRAPPER:wrapper,FAMILY:family_data}
 stamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime());checkpoint=Path('/storage/.aster-checkpoints')/('astertv-v3-dynamic-tv-'+host+'-'+stamp)
 checkpoint.mkdir(mode=0o700)
 evidence={'kind':'astertv-v3-dynamic-tv','host':host,'files':{}}
 for path,data in changed.items():
  rel=str(path.relative_to(ROOT));saved=checkpoint/rel.replace('/','__');saved.write_bytes(originals[path]);saved.chmod(0o600)
  evidence['files'][rel]={'before':sha(originals[path]),'after':sha(data)}
 (checkpoint/'manifest.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
 subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
 try:
  for path,data in changed.items():atomic(path,data)
  for path,data in changed.items():
   if sha(path.read_bytes())!=sha(data):raise RuntimeError('post-write mismatch: '+str(path))
 except Exception:
  for path,data in originals.items():atomic(path,data)
  raise
 finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
 print(json.dumps({'installed':True,'host':host,'checkpoint':str(checkpoint),'manifest_sha256':sha(manifest_data)},sort_keys=True))

if __name__=='__main__':main()
