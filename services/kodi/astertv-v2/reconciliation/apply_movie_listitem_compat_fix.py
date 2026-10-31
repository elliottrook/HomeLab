#!/usr/bin/env python3
"""Use Kodi 22's supported ListItem label2 setter on movie detail rails."""
import hashlib,json,os,socket,subprocess
from pathlib import Path
ADDONS=Path('/storage/.kodi/addons');R=ADDONS/'script.asterruntime';S=R/'aster-global-search-ui22';F=R/'family-manifest.json';M=S/'movie.py';MF=S/'manifest.json'
CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-v2-r11-movie-listitem-compat-20261030')
EXPECTED={M:'49620c1893ab309d4ffa35508267b1e5edb335e701d9fb6e1fb9aec4f5ec8ae9',MF:'730e79b1cb8b7cde6ce51405ab12b1e3edfed379b3d9cd4970e69bdf8106ac31',F:'9a04d50c7a255df7d4285d8463dc1f9ea3ea2d0aa4f7fef71bacf1ebf3040062'}
def sha(d):return hashlib.sha256(d).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def main():
 req={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as c:c.sendall((json.dumps(req)+'\n').encode());a=json.loads(c.recv(4096).decode())
 if a.get('result')!=[]:raise RuntimeError('active-player')
 old={p:p.read_bytes() for p in EXPECTED}
 for p,h in EXPECTED.items():
  if sha(old[p])!=h:raise RuntimeError('unexpected-live-hash:'+str(p))
 text=old[M].decode();text=text.replace("item=xbmcgui.ListItem(label=name,label2=role);item.setArt", "item=xbmcgui.ListItem(label=name);item.setLabel2(role);item.setArt",1)
 text=text.replace("item=xbmcgui.ListItem(label=title,label2=str(year) if year else '')\n                item.setProperty", "item=xbmcgui.ListItem(label=title);item.setLabel2(str(year) if year else '')\n                item.setProperty",1);movie=text.encode()
 manifest=json.loads(old[MF]);row=next(r for r in manifest['files'] if r['path']=='movie.py');row['bytes']=len(movie);row['sha256']=sha(movie);manifest=enc(manifest)
 family=json.loads(old[F]);family['components']['aster-global-search-ui22']['manifest_sha256']=sha(manifest);family=enc(family)
 new={M:movie,MF:manifest,F:family};CHECKPOINT.mkdir(mode=0o700)
 for p,d in old.items():(CHECKPOINT/str(p.relative_to(ADDONS)).replace('/','__')).write_bytes(d)
 subprocess.run(['systemctl','stop','kodi'],check=True)
 try:
  for p,d in new.items():t=p.with_suffix(p.suffix+'.compat');t.write_bytes(d);os.chmod(t,p.stat().st_mode&0o777);os.replace(t,p)
 finally:subprocess.run(['systemctl','start','kodi'],check=True)
 print(json.dumps({'movie':sha(movie),'manifest':sha(manifest),'family':sha(family)},sort_keys=True))
if __name__=='__main__':main()
