"""Exact reversible HP installer for the owned Books recommendation landing."""
import hashlib,json
from pathlib import Path
from digest_news_install import atomic

CHECKPOINT='.aster-checkpoints/aster-books-landing2-20261026'
HELPERS={'books_landing_install.py','deploy_books_landing.py','digest_news_install.py'}

def require(value,code):
 if not value:raise ValueError(code)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unlinked(path):
 path=Path(path);require(not any(x.is_symlink() for x in (path,*path.parents)),'books-landing-linked-path')

def inspect(stage,storage,pin):
 stage,storage=Path(stage),Path(storage);unlinked(stage/'manifest.json')
 require(sha(stage/'manifest.json')==pin,'books-landing-manifest-pin')
 m=json.loads((stage/'manifest.json').read_text());rows=m.get('files',[])
 require(m.get('kind')=='hp-owned-books-landing' and len(rows)==6,'books-landing-contract')
 require(set(m.get('helpers',{}))==HELPERS,'books-landing-helpers')
 for name,digest in m['helpers'].items():require(sha(stage/name)==digest,'books-landing-helper-drift')
 for path,digest in m.get('prerequisite',{}).items():require(sha(storage/path)==digest,'books-landing-prerequisite')
 for row in rows:
  require(set(row)=={'path','sha256','bytes','before_sha256'},'books-landing-row')
  payload=stage/'payload'/row['path'];unlinked(payload);unlinked(storage/row['path'])
  require(sha(payload)==row['sha256'] and payload.stat().st_size==row['bytes'],'books-landing-payload-drift')
 return m

def state(stage,storage,pin):
 m=inspect(stage,storage,pin);cp=Path(storage)/CHECKPOINT
 require(sha(cp/'manifest.json')==pin,'books-landing-recovery-manifest')
 value=json.loads((cp/'state.json').read_text()).get('state')
 require(value in ('prepared','installed','rolled_back'),'books-landing-state')
 for row in m['files']:
  if row['before_sha256'] is not None:require(sha(cp/'original'/row['path'])==row['before_sha256'],'books-landing-recovery-drift')
 return m,value

def active(stage,storage,pin):
 m,value=state(stage,storage,pin);enabled=value=='installed'
 for row in m['files']:
  target=Path(storage)/row['path']
  if enabled:require(target.is_file() and sha(target)==row['sha256'],'books-landing-installed-drift')
  elif row['before_sha256'] is None:require(not target.exists(),'books-landing-new-file-drift')
  else:require(sha(target)==row['before_sha256'],'books-landing-installed-drift')
 return enabled

def restore(m,storage,cp):
 for row in m['files']:
  target=storage/row['path']
  if row['before_sha256'] is None:
   if target.exists():
    require(target.is_file() and sha(target)==row['sha256'],'books-landing-rollback-drift');target.unlink()
  else:
   require(target.exists() and sha(target) in {row['sha256'],row['before_sha256']},'books-landing-rollback-drift')
   atomic(target,(cp/'original'/row['path']).read_bytes())
 feed=storage/m['feed'];atomic(feed,(cp/'original-feed.json').read_bytes())

def run(mode,stage,storage,pin,*,idle):
 require(mode in ('install','verify','rollback'),'books-landing-mode')
 stage,storage=Path(stage),Path(storage);m=inspect(stage,storage,pin);require(idle(),'books-landing-home-idle-required')
 cp=storage/CHECKPOINT
 if mode=='verify':return dict(verified=True,active=active(stage,storage,pin),files=6)
 if mode=='rollback':
  _,value=state(stage,storage,pin);require(value in ('prepared','installed'),'books-landing-not-active')
  restore(m,storage,cp);atomic(cp/'state.json',b'{"state":"rolled_back"}\n');require(not active(stage,storage,pin),'books-landing-rollback-failed')
  return dict(rolled_back=True,files=6)
 require(not cp.exists(),'books-landing-checkpoint-exists')
 for row in m['files']:
  target=storage/row['path']
  if row['before_sha256'] is None:require(not target.exists(),'books-landing-new-file-exists')
  else:require(target.is_file() and sha(target)==row['before_sha256'],'books-landing-exact-predecessor')
 feed=storage/m['feed'];require(feed.is_file(),'books-landing-feed-required')
 cp.mkdir(parents=True,mode=0o700);atomic(cp/'manifest.json',(stage/'manifest.json').read_bytes())
 for row in m['files']:
  if row['before_sha256'] is not None:atomic(cp/'original'/row['path'],(storage/row['path']).read_bytes())
 atomic(cp/'original-feed.json',feed.read_bytes());atomic(cp/'state.json',b'{"state":"prepared"}\n')
 try:
  require(idle(),'books-landing-home-idle-required')
  for row in m['files']:atomic(storage/row['path'],(stage/'payload'/row['path']).read_bytes())
  atomic(cp/'state.json',b'{"state":"installed"}\n');require(active(stage,storage,pin),'books-landing-install-failed')
 except Exception:
  restore(m,storage,cp);atomic(cp/'state.json',b'{"state":"rolled_back"}\n');raise
 return dict(installed=True,files=6,checkpoint_verified=True)
