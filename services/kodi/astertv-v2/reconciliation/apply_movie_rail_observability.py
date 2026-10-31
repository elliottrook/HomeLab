#!/usr/bin/env python3
"""Add content-free movie-rail readiness evidence and a visible safe fallback."""
import hashlib,json,os,socket,subprocess
from pathlib import Path
A=Path('/storage/.kodi/addons');R=A/'script.asterruntime';S=R/'aster-global-search-ui22';M=S/'movie.py';MF=S/'manifest.json';F=R/'family-manifest.json';C=Path('/storage/.aster-checkpoints/astertv-v2-r11-movie-rail-observability-20261030')
E={M:'c8a8ecea4466405514ed6d199ee4dce870f6216cef71c420dce20db5e5b9e33a',MF:'0e3e0233829cf5a408e1ae413bcbe95c73dd73eaaa1141d1d530149f050515da',F:'59954d7cce5da40a404fc2732eb17b598d33d9e66d40d32dae2e1d14e17bf5df'}
def h(d):return hashlib.sha256(d).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def main():
 q={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as c:c.sendall((json.dumps(q)+'\n').encode());a=json.loads(c.recv(4096).decode())
 if a.get('result')!=[]:raise RuntimeError('active-player')
 o={p:p.read_bytes() for p in E}
 for p,x in E.items():
  if h(o[p])!=x:raise RuntimeError('hash:'+str(p))
 t=o[M].decode();old="""            people,related=enrichment(value)
            cast_control=window.getControl(500);cast_control.reset();cast_items=[]
""";new="""            people,related=enrichment(value)
            xbmc.log('AsterMovieRails: model people='+str(len(people))+' related='+str(len(related)),xbmc.LOGINFO)
            cast_control=window.getControl(500);cast_control.reset();cast_items=[]
"""
 if t.count(old)!=1:raise RuntimeError('model-anchor')
 t=t.replace(old,new,1);old="""            if related_items:related_control.addItems(related_items)
            window.setProperty('Movie.CastVisible','true' if people else 'false')
""";new="""            if related_items:related_control.addItems(related_items)
            xbmc.log('AsterMovieRails: controls cast='+str(cast_control.size())+' related='+str(related_control.size()),xbmc.LOGINFO)
            window.setProperty('Movie.CastVisible','true' if people else 'false')
"""
 if t.count(old)!=1:raise RuntimeError('control-anchor')
 m=t.replace(old,new,1).encode();mf=json.loads(o[MF]);row=next(r for r in mf['files'] if r['path']=='movie.py');row['bytes']=len(m);row['sha256']=h(m);mf=enc(mf);f=json.loads(o[F]);f['components']['aster-global-search-ui22']['manifest_sha256']=h(mf);f=enc(f);n={M:m,MF:mf,F:f};C.mkdir(mode=0o700)
 for p,d in o.items():(C/str(p.relative_to(A)).replace('/','__')).write_bytes(d)
 subprocess.run(['systemctl','stop','kodi'],check=True)
 try:
  for p,d in n.items():z=p.with_suffix(p.suffix+'.observe');z.write_bytes(d);os.chmod(z,p.stat().st_mode&0o777);os.replace(z,p)
 finally:subprocess.run(['systemctl','start','kodi'],check=True)
 print(json.dumps({'movie':h(m),'manifest':h(mf),'family':h(f)},sort_keys=True))
if __name__=='__main__':main()
