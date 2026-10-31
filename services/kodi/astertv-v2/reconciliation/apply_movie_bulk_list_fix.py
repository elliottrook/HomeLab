#!/usr/bin/env python3
"""Populate Kodi custom-window movie rails using atomic ControlList.addItems."""
import hashlib,json,os,socket,subprocess
from pathlib import Path
A=Path('/storage/.kodi/addons');R=A/'script.asterruntime';S=R/'aster-global-search-ui22';M=S/'movie.py';MF=S/'manifest.json';F=R/'family-manifest.json';C=Path('/storage/.aster-checkpoints/astertv-v2-r11-movie-bulk-lists-20261030')
E={M:'5ce2305c1f3ee732121e3bd3a5052d6d1def4a14650b5d483e6d65c753bf949c',MF:'ee0dc7ccebdd17ebc431e5094dfa89fd69865b090d4d7c7696b7cbf065ecc7f3',F:'6af5d6a0c45837eafdb1b9a57e10e66cbb282c958285a4b25447f394bcdbf93e'}
def h(d):return hashlib.sha256(d).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def main():
 q={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as c:c.sendall((json.dumps(q)+'\n').encode());a=json.loads(c.recv(4096).decode())
 if a.get('result')!=[]:raise RuntimeError('active-player')
 o={p:p.read_bytes() for p in E}
 for p,x in E.items():
  if h(o[p])!=x:raise RuntimeError('hash:'+str(p))
 t=o[M].decode();old="""            cast_control=window.getControl(500);cast_control.reset()
            for name,role,thumb in people:
                item=xbmcgui.ListItem(label=name);item.setProperty('Role',role);item.setArt({'thumb':thumb or 'special://skin/media/aster-compass-128.png'});cast_control.addItem(item)
            related_control=window.getControl(501);related_control.reset()
            for identity,title,thumb,year in related:
                item=xbmcgui.ListItem(label=title);item.setProperty('Year',str(year) if year else '')
                item.setProperty('MovieId',str(identity));item.setArt({'thumb':thumb or 'special://skin/media/08-film.png'});related_control.addItem(item)
""";new="""            cast_control=window.getControl(500);cast_control.reset();cast_items=[]
            for name,role,thumb in people:
                item=xbmcgui.ListItem(label=name);item.setProperty('Role',role);item.setArt({'thumb':thumb or 'special://skin/media/aster-compass-128.png'});cast_items.append(item)
            if cast_items:cast_control.addItems(cast_items)
            related_control=window.getControl(501);related_control.reset();related_items=[]
            for identity,title,thumb,year in related:
                item=xbmcgui.ListItem(label=title);item.setProperty('Year',str(year) if year else '')
                item.setProperty('MovieId',str(identity));item.setArt({'thumb':thumb or 'special://skin/media/08-film.png'});related_items.append(item)
            if related_items:related_control.addItems(related_items)
"""
 if t.count(old)!=1:raise RuntimeError('bulk-anchor')
 m=t.replace(old,new,1).encode();mf=json.loads(o[MF]);row=next(r for r in mf['files'] if r['path']=='movie.py');row['bytes']=len(m);row['sha256']=h(m);mf=enc(mf);f=json.loads(o[F]);f['components']['aster-global-search-ui22']['manifest_sha256']=h(mf);f=enc(f);n={M:m,MF:mf,F:f};C.mkdir(mode=0o700)
 for p,d in o.items():(C/str(p.relative_to(A)).replace('/','__')).write_bytes(d)
 subprocess.run(['systemctl','stop','kodi'],check=True)
 try:
  for p,d in n.items():z=p.with_suffix(p.suffix+'.bulk');z.write_bytes(d);os.chmod(z,p.stat().st_mode&0o777);os.replace(z,p)
 finally:subprocess.run(['systemctl','start','kodi'],check=True)
 print(json.dumps({'movie':h(m),'manifest':h(mf),'family':h(f)},sort_keys=True))
if __name__=='__main__':main()
