#!/usr/bin/env python3
"""Restore the missing explicit entry point in Aster News on both clients."""
import hashlib,json,os,socket,tempfile,time
from pathlib import Path
ROOT=Path('/storage/.kodi/addons');WRAPPER=ROOT/'skin.asterhome/tools/aster_v2_digest.py';FAMILY=ROOT/'script.asterruntime/family-manifest.json';PLAYER=ROOT/'script.asterruntime/aster-digest-player8'
BASELINES={
 '4958ec39e5dc76e089d7a856fe15b842046312b9f5de15b8e0201cb40599ce03',
 '401841eb166fe7a8e3a77b2bdd5bc4f74aebe50b324eb6e45744d3d53a0063f5',
 'efe1cbb01ae60ac3baaa25a4778344fec70c1af962d51caf72fe597595faaaa8',
}
PIN='9e3644b7d012bc7610f7366608456ce06ffe1d8b6eee315574bb762d5a186e9c'
STALE_PIN='d10c10756f88493e5c28be039135d1d84d7cd6b2b5c750adc17ac9fa3a4dda37'
def sha(b):return hashlib.sha256(b).hexdigest()
def atomic(p,b):
 fd,t=tempfile.mkstemp(prefix='.aster-news-entry-',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.chmod(t,0o644);os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def main():
 host=socket.gethostname()
 if host not in ('AsterTV-Bedroom','AsterTV-Family'):raise RuntimeError('target refused')
 raw=(PLAYER/'manifest.json').read_bytes()
 if sha(raw)!=PIN:raise RuntimeError('player manifest drift')
 for row in json.loads(raw)['files']:
  p=PLAYER/row['path']
  if not p.is_file() or sha(p.read_bytes())!=row['sha256']:raise RuntimeError('player member drift: '+row['path'])
 old=WRAPPER.read_bytes()
 if sha(old) not in BASELINES:raise RuntimeError('launcher baseline drift')
 source=old.decode()
 if "PIN = '"+PIN+"'" not in source:
  if source.count(STALE_PIN)!=1:raise RuntimeError('launcher pin mismatch')
  source=source.replace(STALE_PIN,PIN)
 if "Aster News launcher refused:" not in source:
  needle="    except (OSError, ValueError, KeyError, RuntimeError, TypeError):\n        xbmcgui.Dialog().notification('Aster News', 'Briefing unavailable or changed. Refresh News and try again when idle.')"
  replacement="    except (OSError, ValueError, KeyError, RuntimeError, TypeError) as error:\n        xbmc.log('Aster News launcher refused: '+repr(error), xbmc.LOGERROR)\n        xbmcgui.Dialog().notification('Aster News', 'Briefing unavailable or changed. Refresh News and try again when idle.')"
  if source.count(needle)!=1:raise RuntimeError('exception boundary drift')
  source=source.replace(needle,replacement)
 entry="\n\nif __name__ == '__main__':\n    if len(sys.argv) == 2:\n        main(sys.argv[1])\n"
 if "if __name__ == '__main__':" in source:raise RuntimeError('entry already present')
 new=(source.rstrip()+entry).encode();family_old=FAMILY.read_bytes();family=json.loads(family_old);family['skin']['tools/aster_v2_digest.py']=sha(new);family_new=(json.dumps(family,indent=2,sort_keys=True)+'\n').encode()
 cp=Path('/storage/.aster-checkpoints')/('astertv-news-entry-'+host+'-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime()));cp.mkdir(mode=0o700);(cp/'launcher.before').write_bytes(old);(cp/'family.before').write_bytes(family_old)
 atomic(WRAPPER,new);atomic(FAMILY,family_new);print(json.dumps({'installed':True,'host':host,'checkpoint':str(cp),'wrapper_sha256':sha(new)},sort_keys=True))
if __name__=='__main__':main()
