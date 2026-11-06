"""Build exact revision3 before any model session; preserves prior revisions."""
from pathlib import Path
import base64,json,hashlib
here=Path(__file__).resolve().parent
old={'model_trial.py':'30308259ef61c2f6f4c379f94699161a6f154029580a3b102640d9fff3e8fb04','namespace_mount.py':'25adc8b02ee3aec9508283b92bfceb87b56183da2698a9f246728604d9f7397c','fixed_command.py':'9fd4e5746363e7cbdcac0d121d15cdac4ce990c24a1e988bc8b98faad8bcf260','guest_requests.py':'dbc596c5b77a8ea9359868798d621ff951c331754b2b4968c177b80d079e3dca'}
new=json.loads((here/'manifest.json').read_text())
files={n:base64.b64encode((here/n).read_bytes()).decode() for n in ('model_trial.py','namespace_mount.py','guest_supervisor.py')}
guestfiles={n:base64.b64encode((here/n).read_bytes()).decode() for n in ('fixed_command.py','guest_supervisor.py')}
script=r'''
import base64,hashlib,json,os,sys,time,subprocess
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');sys.path.insert(0,str(BASE))
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes
from lab_hours_exclusive_session import canonical
from lab_hours_reservations import ReservationStore
ROOT=Path('/var/lib/local-ai-lab');B='b60-exclusive-20261106-day-r1';HERE=BASE.parent/'model-trial-20261106'
def replace(p,raw):
 t=p.with_name(p.name+'.private-unit-update-tmp');fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.replace(t,p);fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
def call(c):
 p=subprocess.run(c,capture_output=True,text=True,timeout=30);assert p.returncode==0;return p.stdout.strip()
with host_exclusion(ROOT):
 assert not any(p.exists() or p.is_symlink() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 assert not (ROOT/'exclusive-sessions'/B/'session.json').exists()
 row=ReservationStore(ROOT/'reservations',expected_uid=0).get(B);assert row['state']=='reserved' and time.time()+600<row['start_epoch']
 actual={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in HERE.glob('*.py')};assert actual==OLD
 assert json.loads(protected_bytes(HERE/'manifest.json'))==OLD
 cardpath=ROOT/'model-trial-cards'/(B+'.json');card=json.loads(protected_bytes(cardpath));assert card['source_sha256']==OLD
 rp=ROOT/'arming-receipts'/(B+'-model-revision2.json');previous=protected_bytes(rp);assert hashlib.sha256(previous).hexdigest()=='3e88fe8fea1e4359a80f963d2cfd1f174022b8af54cf5959e9b3da7f3a27f308'
 arm=json.loads(previous)
 for n,sha in arm['unit_sha256'].items():assert hashlib.sha256(Path('/etc/systemd/system',n).read_bytes()).hexdigest()==sha
 paths={n:HERE/n for n in FILES};paths.update(manifest=HERE/'manifest.json',card=cardpath)
 oldbytes={n:protected_bytes(p,executable=n.endswith('.py'),maximum=262144) if p.exists() else None for n,p in paths.items()}
 assert oldbytes['guest_supervisor.py'] is None and all(v is not None for k,v in oldbytes.items() if k!='guest_supervisor.py')
 checkpoint=ROOT/'model-trial-source-checkpoint-private-unit-v3';checkpoint.mkdir(mode=0o700)
 for n,raw in oldbytes.items():
  if raw is not None:
   fd=os.open(checkpoint/n,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
   with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(checkpoint,os.O_RDONLY);os.fsync(fd);os.close(fd)
 journal=checkpoint/'journal.json';replace(journal,canonical({'state':'pending','old':OLD,'new':NEW,'booking_id':B,'new_host_file':'guest_supervisor.py'}))
 # Non-secret immutable source only. No key file or model is accessed here.
 guestcode="from pathlib import Path;import os,json,base64,hashlib;d=Path('/usr/local/libexec/local-ai-lease/model-trial-20261106');s=d.lstat();assert d.is_dir() and not d.is_symlink() and s.st_uid==0 and s.st_mode&0o022==0;files="+repr(GUEST_FILES)+";\\nfor n,v in files.items():\\n p=d/n;assert not p.exists() and not p.is_symlink();fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o644);f=os.fdopen(fd,'wb');f.write(base64.b64decode(v));f.flush();os.fsync(f.fileno());f.close()\\nos.chmod(d,0o755);print(json.dumps({n:hashlib.sha256((d/n).read_bytes()).hexdigest() for n in files}))"
 guestcode=guestcode.replace('\\n','\n')
 try:
  guest=json.loads(call(['pct','exec','110','--','python3','-B','-c',guestcode]));assert guest=={n:NEW[n] for n in GUEST_FILES}
  for n,encoded in FILES.items():
   raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==NEW[n];replace(HERE/n,raw)
  replace(HERE/'manifest.json',canonical(NEW));card['source_sha256']=NEW;replace(cardpath,canonical(card))
  sys.path.insert(0,str(HERE));from model_trial import initialize,card_for
  assert initialize()==NEW and card_for(B)==card
  arm['source_sha256']=NEW;arm['model_card_sha256']=hashlib.sha256(canonical(card)).hexdigest();arm['predecessor_arming_sha256']=hashlib.sha256(previous).hexdigest();arm['revision']=3;arm['source_correction']='candidate-only-private-service-namespace';arm['verified_epoch']=int(time.time());arm['guest_supplementary_source_sha256']=guest
  nr=ROOT/'arming-receipts'/(B+'-model-revision3.json');assert not nr.exists();replace(nr,canonical(arm))
  replace(journal,canonical({'state':'complete','old':OLD,'new':NEW,'booking_id':B,'arming_sha256':hashlib.sha256(canonical(arm)).hexdigest()}))
  print(json.dumps({'state':'updated-and-reverified','booking_id':B,'source_sha256':NEW,'arming_receipt':str(nr),'arming_sha256':hashlib.sha256(canonical(arm)).hexdigest(),'timers_unchanged':True,'no_model_or_stack_drain':True},sort_keys=True))
 except BaseException:
  for n,p in paths.items():
   if oldbytes[n] is not None:replace(p,oldbytes[n])
   elif p.exists():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==NEW[n];p.unlink()
  assert all(protected_bytes(p,executable=n.endswith('.py'),maximum=262144)==raw if raw is not None else not p.exists() for n,p in paths.items() for raw in [oldbytes[n]])
  replace(journal,canonical({'state':'rolled-back','old':OLD,'new':NEW,'booking_id':B,'nonsecret_guest_source_may_remain_inactive':True}));raise
'''
output='OLD='+repr(old)+'\nNEW='+repr(new)+'\nFILES='+repr(files)+'\nGUEST_FILES='+repr(guestfiles)+'\n'+script
Path('/private/tmp/b60-model-trial-private-unit-update.py').write_text(output)
print(json.dumps({'updater_sha256':hashlib.sha256(output.encode()).hexdigest(),'new':new},sort_keys=True))
