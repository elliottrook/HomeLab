#!/usr/bin/env python3
"""Wait for Kodi's movie XML controls before populating its detail rails."""
import hashlib,json,os,socket,subprocess
from pathlib import Path
A=Path('/storage/.kodi/addons');R=A/'script.asterruntime';S=R/'aster-global-search-ui22';M=S/'movie.py';MF=S/'manifest.json';F=R/'family-manifest.json';C=Path('/storage/.aster-checkpoints/astertv-v2-r11-movie-window-ready-20261030')
E={M:'5b46e169c3e89965592f8905ba9c85b5b293d82fb579aaf0baf01b43146b9b92',MF:'06bb52d0f45777fcdf792c3934c0ec81178f0507ffe3e180e24c04b7145a9f94',F:'0d25f63adbfcd9ddb19bd155a0331bc9ffc3f404b038f701bc6ebd54926b717a'}
def h(d):return hashlib.sha256(d).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def main():
 q={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as c:c.sendall((json.dumps(q)+'\n').encode());a=json.loads(c.recv(4096).decode())
 if a.get('result')!=[]:raise RuntimeError('active-player')
 o={p:p.read_bytes() for p in E}
 for p,x in E.items():
  if h(o[p])!=x:raise RuntimeError('hash:'+str(p))
 t=o[M].decode();old='        window=xbmcgui.Window(11130)\n        def render():';new='        window=xbmcgui.Window(11130)\n        xbmc.sleep(300)  # Kodi publishes the custom ID before its XML controls settle.\n        def render():'
 if t.count(old)!=1:raise RuntimeError('ready-anchor')
 m=t.replace(old,new,1).encode();mf=json.loads(o[MF]);row=next(r for r in mf['files'] if r['path']=='movie.py');row['bytes']=len(m);row['sha256']=h(m);mf=enc(mf);f=json.loads(o[F]);f['components']['aster-global-search-ui22']['manifest_sha256']=h(mf);f=enc(f);n={M:m,MF:mf,F:f};C.mkdir(mode=0o700)
 for p,d in o.items():(C/str(p.relative_to(A)).replace('/','__')).write_bytes(d)
 subprocess.run(['systemctl','stop','kodi'],check=True)
 try:
  for p,d in n.items():z=p.with_suffix(p.suffix+'.ready');z.write_bytes(d);os.chmod(z,p.stat().st_mode&0o777);os.replace(z,p)
 finally:subprocess.run(['systemctl','start','kodi'],check=True)
 print(json.dumps({'movie':h(m),'manifest':h(mf),'family':h(f)},sort_keys=True))
if __name__=='__main__':main()
