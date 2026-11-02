#!/usr/bin/env python3
"""Install the dedicated Aster trailer glyph after the TV control repair."""
import hashlib,json,os,socket,subprocess,tempfile,time
from pathlib import Path

ROOT=Path('/storage/.kodi/addons');HERE=Path(__file__).resolve().parent
SERIES=ROOT/'script.asterruntime/aster-series-preview24'
XML=SERIES/'resources/skins/Default/1080i/SeriesPreview.xml';MANIFEST=SERIES/'manifest.json'
WRAPPER=ROOT/'skin.asterhome/tools/aster_v2_series.py';FAMILY=ROOT/'script.asterruntime/family-manifest.json'
ICON=ROOT/'skin.asterhome/media/player-controls/trailer.png'
EXPECTED={
 XML:'5eedaee7d590fca96bc0ae869b7421f6a741b65b00423cfcd3948c0e1b5851c5',
 MANIFEST:'de9e4ee20bfe38c44d07a5dec26b2548dbd6862a6dc8e78236ca84c07f232bb8',
}
def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(data):return (json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix='.aster-trailer-',dir=path.parent)
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
 active_players();originals={p:p.read_bytes() for p in (XML,MANIFEST,WRAPPER,FAMILY)}
 for path,expected in EXPECTED.items():
  if sha(originals[path])!=expected:raise RuntimeError('baseline drift: '+str(path))
 xml=(HERE/'aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml').read_bytes()
 icon=(HERE/'skin.asterhome/media/player-controls/trailer.png').read_bytes()
 if b'player-controls/trailer.png' not in xml or sha(icon)!='b2d7d331f02ddbced8c5eb875c43d3d9a0bdcf1c758cd9e4369ed38392730c71':raise RuntimeError('candidate drift')
 manifest=json.loads(originals[MANIFEST]);row=next(r for r in manifest['files'] if r['path']=='resources/skins/Default/1080i/SeriesPreview.xml');row.update(bytes=len(xml),sha256=sha(xml));manifest_data=encoded(manifest)
 wrapper=originals[WRAPPER].decode()
 if wrapper.count(EXPECTED[MANIFEST])!=1:raise RuntimeError('wrapper pin drift')
 wrapper_data=wrapper.replace(EXPECTED[MANIFEST],sha(manifest_data)).encode();family=json.loads(originals[FAMILY]);family['components']['aster-series-preview24']={'files':9,'manifest_sha256':sha(manifest_data)};family['skin']['tools/aster_v2_series.py']=sha(wrapper_data);family_data=encoded(family)
 changed={XML:xml,MANIFEST:manifest_data,WRAPPER:wrapper_data,FAMILY:family_data,ICON:icon};stamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime());checkpoint=Path('/storage/.aster-checkpoints')/('astertv-v3-trailer-icon-'+host+'-'+stamp);checkpoint.mkdir(mode=0o700)
 for path in (XML,MANIFEST,WRAPPER,FAMILY):saved=checkpoint/str(path.relative_to(ROOT)).replace('/','__');saved.write_bytes(originals[path]);saved.chmod(0o600)
 subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
 try:
  for path,data in changed.items():atomic(path,data)
  for path,data in changed.items():
   if sha(path.read_bytes())!=sha(data):raise RuntimeError('post-write mismatch: '+str(path))
 except Exception:
  for path,data in originals.items():atomic(path,data)
  if ICON.exists():ICON.unlink()
  raise
 finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
 print(json.dumps({'installed':True,'host':host,'checkpoint':str(checkpoint),'manifest_sha256':sha(manifest_data),'xml_sha256':sha(xml),'icon_sha256':sha(icon)},sort_keys=True))
if __name__=='__main__':main()
