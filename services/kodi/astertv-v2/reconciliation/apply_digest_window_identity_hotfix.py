#!/usr/bin/env python3
"""One-time r10 upgrade for Kodi 22 Digest WindowXML identity timing."""

import hashlib, json, os, socket, subprocess, tempfile
from pathlib import Path

ROOT=Path('/storage/.kodi/addons'); RUNTIME=ROOT/'script.asterruntime'; SKIN=ROOT/'skin.asterhome'
PLAYER=RUNTIME/'aster-digest-player8/default.py'; PM=RUNTIME/'aster-digest-player8/manifest.json'
READER=RUNTIME/'aster-digest-reader6/default.py'; RM=RUNTIME/'aster-digest-reader6/manifest.json'
WRAPPER=SKIN/'tools/aster_v2_digest.py'; DIGEST=SKIN/'1080i/custom_1111_digest.xml'; FAMILY=RUNTIME/'family-manifest.json'
CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-v2-r10-digest-window-20261030')
EXPECTED={PLAYER:'3e089588091c2959804daee23ab80b042fb0963d7c029f9534317e6665f73d5c',
 PM:'eb9d4d69416f51f8eb97227644d19da8a6f68decefee87446bade083229f16c5',
 READER:'32c5b955ee6551d3a9673889dabe2d421352274946ceaf5ce9aeb0bbcb37d1c0',
 RM:'0cc53c96055569bd41ba05024f18f1ac9879b0ece1f31490091afdaf9a560288',
 WRAPPER:'c9ddfb5d26f217c09ed7067ba17306dc1888f0ba81b58dbf20a61017e2003982',
 DIGEST:'514643bdbb33cc69bf76a2550c2086332a875128a237d7709c940232c382ee0c',
 FAMILY:'926b0c72c589e8a7d541d2cce5c6ed2db09eb14b0eaf7a501a57fcc6442c1d4c'}

def sha(data):return hashlib.sha256(data).hexdigest()
def encode(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def replace(data,old,new):
 text=data.decode()
 if text.count(old)!=1:raise RuntimeError('replacement-count')
 return text.replace(old,new,1).encode()
def atomic(path,data):
 fd,tmp=tempfile.mkstemp(prefix='.aster-digest-window-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
  os.chmod(tmp,0o644);os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def no_player():
 q={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as s:
  s.sendall((json.dumps(q)+'\n').encode())
  if json.loads(s.recv(4096)).get('result')!=[]:raise RuntimeError('active-player')
def repin(manifest_data,member):
 value=json.loads(manifest_data);row=next(x for x in value['files'] if x['path']=='default.py')
 row['bytes']=len(member);row['sha256']=sha(member);return encode(value)

def main():
 if os.uname().nodename!='AsterTV' or CHECKPOINT.exists():raise RuntimeError('lab-checkpoint-guard')
 originals={p:p.read_bytes() for p in EXPECTED}
 if any(sha(originals[p])!=h for p,h in EXPECTED.items()):raise RuntimeError('unexpected-r10-state')
 no_player()
 player=replace(originals[PLAYER],'''        window.show()
        until(lambda:window.identity is not None, 'player-ui-not-ready', 4)
''','''        window.show()
        # onInit can still see the source custom window on Kodi 22.  Resolve
        # the allocated WindowXML identity only after the visible window has
        # actually changed, as the stable Series page already does.
        until(lambda: xbmcgui.getCurrentWindowId() not in (0, 10000, source_window),
              'player-ui-not-ready', 4)
        window.identity = xbmcgui.getCurrentWindowId()
        xbmcgui.Window(10000).setProperty('AsterDigest.PlayerWindow', str(window.identity))
''')
 reader=replace(originals[READER],'''        window.show()
        monitor = xbmc.Monitor()
        try:
            for _ in range(80):
                if window.identity is not None: break
                if monitor.waitForAbort(.05): return
''','''        window.show()
        # WindowXML.onInit may report the source page before Kodi publishes
        # the allocated reader ID.  Discard that provisional identity and
        # wait for the actual visible WindowXML.
        window.identity = None
        monitor = xbmc.Monitor()
        try:
            for _ in range(80):
                current = xbmcgui.getCurrentWindowId()
                if current not in (0, 10000, source_id):
                    window.identity = current
                    home.setProperty('AsterDigest.ReaderWindow', str(current))
                    break
                if monitor.waitForAbort(.05): return
''')
 if sha(player)!='e4ca65d2804d3db148526f5ebf15ebcaaed1d034bc9efc1eeaafcbfb098a7008' or sha(reader)!='abef059485c8caf32d193574469cdd9d96cb62cc52d9574a0eae2d71f25b38fa':raise RuntimeError('candidate-hash')
 pm=repin(originals[PM],player);rm=repin(originals[RM],reader);pp=sha(pm);rp=sha(rm)
 wrapper=replace(originals[WRAPPER],EXPECTED[PM],pp);digest=replace(originals[DIGEST],EXPECTED[RM],rp)
 family=json.loads(originals[FAMILY]);family['components']['aster-digest-player8']['manifest_sha256']=pp;family['components']['aster-digest-reader6']['manifest_sha256']=rp;family['skin']['tools/aster_v2_digest.py']=sha(wrapper);family['skin']['1080i/custom_1111_digest.xml']=sha(digest);family=encode(family)
 candidates={PLAYER:player,PM:pm,READER:reader,RM:rm,WRAPPER:wrapper,DIGEST:digest,FAMILY:family}
 CHECKPOINT.mkdir(mode=0o700)
 for path,data in originals.items():
  saved=CHECKPOINT/str(path.relative_to(ROOT)).replace('/','__');saved.write_bytes(data);saved.chmod(0o600)
 (CHECKPOINT/'manifest.json').write_text(json.dumps({'kind':'astertv-v2-r10-digest-window','files':{str(p.relative_to(ROOT)):{'before':sha(originals[p]),'after':sha(candidates[p])} for p in candidates}},indent=2,sort_keys=True)+'\n');(CHECKPOINT/'manifest.json').chmod(0o600)
 subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
 try:
  for p,d in candidates.items():atomic(p,d)
  if any(sha(p.read_bytes())!=sha(d) for p,d in candidates.items()):raise RuntimeError('install-verify')
 except Exception:
  for p,d in originals.items():atomic(p,d)
  raise
 finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
 print(json.dumps({'installed':True,'player_pin':pp,'reader_pin':rp,'family_sha256':sha(family),'checkpoint':str(CHECKPOINT)},sort_keys=True))
if __name__=='__main__':main()
