#!/usr/bin/env python3
"""Remove unsupported secondary-label calls from Kodi 22 movie rail items."""
import hashlib,json,os,socket,subprocess
from pathlib import Path
A=Path('/storage/.kodi/addons');R=A/'script.asterruntime';S=R/'aster-global-search-ui22';M=S/'movie.py';MF=S/'manifest.json';F=R/'family-manifest.json';C=Path('/storage/.aster-checkpoints/astertv-v2-r11-movie-listitem-label-20261030')
E={M:'8ba983e5a71dd588596c3886a60ef9decea383c75005aa5fbebcf3c55ee61914',MF:'3942c80701e79756be09c1043d9f34042bdc5975b7692ec72151de254e57ab28',F:'63d802bae68b9454371019ea59897151398b1bdc762024c40f0d88ce301b2444'}
def h(d):return hashlib.sha256(d).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def main():
 q={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as c:c.sendall((json.dumps(q)+'\n').encode());a=json.loads(c.recv(4096).decode())
 if a.get('result')!=[]:raise RuntimeError('active-player')
 o={p:p.read_bytes() for p in E}
 for p,x in E.items():
  if h(o[p])!=x:raise RuntimeError('hash:'+str(p))
 t=o[M].decode().replace("item=xbmcgui.ListItem(label=name);item.setLabel2(role);item.setArt", "item=xbmcgui.ListItem(label=name);item.setProperty('Role',role);item.setArt",1).replace("item=xbmcgui.ListItem(label=title);item.setLabel2(str(year) if year else '')\n                item.setProperty", "item=xbmcgui.ListItem(label=title);item.setProperty('Year',str(year) if year else '')\n                item.setProperty",1);m=t.encode()
 mf=json.loads(o[MF]);row=next(r for r in mf['files'] if r['path']=='movie.py');row['bytes']=len(m);row['sha256']=h(m);mf=enc(mf)
 f=json.loads(o[F]);f['components']['aster-global-search-ui22']['manifest_sha256']=h(mf);f=enc(f);n={M:m,MF:mf,F:f};C.mkdir(mode=0o700)
 for p,d in o.items():(C/str(p.relative_to(A)).replace('/','__')).write_bytes(d)
 subprocess.run(['systemctl','stop','kodi'],check=True)
 try:
  for p,d in n.items():z=p.with_suffix(p.suffix+'.label');z.write_bytes(d);os.chmod(z,p.stat().st_mode&0o777);os.replace(z,p)
 finally:subprocess.run(['systemctl','start','kodi'],check=True)
 print(json.dumps({'movie':h(m),'manifest':h(mf),'family':h(f)},sort_keys=True))
if __name__=='__main__':main()
