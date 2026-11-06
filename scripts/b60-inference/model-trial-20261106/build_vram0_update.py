"""Exact pre-trial model residency observer correction; no timer or entry change."""
from pathlib import Path
import base64,json,hashlib
here=Path(__file__).resolve().parent
old={'model_trial.py':'0610114d18fab5ec265ea65644cb8a85c89249445749bdfac549fe372e1f10e9','namespace_mount.py':'031df2fb964c264c168cfd313de816391cb49d735701b17821edae2077a72566','fixed_command.py':'9fd4e5746363e7cbdcac0d121d15cdac4ce990c24a1e988bc8b98faad8bcf260','guest_requests.py':'dbc596c5b77a8ea9359868798d621ff951c331754b2b4968c177b80d079e3dca','guest_supervisor.py':'ca23df9ec859044cee61737be476a8eab53f4b30a30efbf3b1421863e8fe0449'}
new=json.loads((here/'manifest.json').read_text())
files={n:base64.b64encode((here/n).read_bytes()).decode() for n in ('model_trial.py',)}
code=r'''
import base64,hashlib,json,os,sys,time,subprocess
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');sys.path.insert(0,str(BASE))
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes
from lab_hours_exclusive_session import canonical
from lab_hours_reservations import ReservationStore
ROOT=Path('/var/lib/local-ai-lab');B='b60-exclusive-20261106-day-r1';HERE=BASE.parent/'model-trial-20261106'
def replace(p,raw):
 tmp=p.with_name(p.name+'.propagation-update-tmp');fd=os.open(tmp,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p);fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
with host_exclusion(ROOT):
 assert not any(p.exists() or p.is_symlink() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
 assert not (ROOT/'exclusive-sessions'/B/'session.json').exists()
 row=ReservationStore(ROOT/'reservations',expected_uid=0).get(B);assert row['state']=='reserved' and time.time()+600<row['start_epoch']
 actual={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in HERE.glob('*.py')};assert actual==OLD
 assert json.loads(protected_bytes(HERE/'manifest.json'))==OLD
 cardpath=ROOT/'model-trial-cards'/(B+'.json');card=json.loads(protected_bytes(cardpath));assert card['source_sha256']==OLD
 receiptpath=ROOT/'arming-receipts'/(B+'-model-revision4.json');previous=protected_bytes(receiptpath);assert hashlib.sha256(previous).hexdigest()=='e98cbce6eeccd0ab6079da8ad922539efc847a6c1e72f9870a5c8a354bfc0af3'
 arm=json.loads(previous)
 for n,sha in arm['unit_sha256'].items():assert hashlib.sha256(Path('/etc/systemd/system',n).read_bytes()).hexdigest()==sha
 paths={n:HERE/n for n in FILES};paths.update(manifest=HERE/'manifest.json',card=cardpath)
 oldbytes={n:protected_bytes(p,executable=n.endswith('.py'),maximum=262144) for n,p in paths.items()}
 checkpoint=ROOT/'model-trial-source-checkpoint-vram0-v5';checkpoint.mkdir(mode=0o700)
 for n,raw in oldbytes.items():
  fd=os.open(checkpoint/n,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(checkpoint,os.O_RDONLY);os.fsync(fd);os.close(fd)
 journal=checkpoint/'journal.json';replace(journal,canonical({'state':'pending','old':OLD,'new':NEW,'booking_id':B}))
 try:
  for n,encoded in FILES.items():
   raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==NEW[n];replace(HERE/n,raw)
  replace(HERE/'manifest.json',canonical(NEW));card['source_sha256']=NEW;replace(cardpath,canonical(card))
  sys.path.insert(0,str(HERE));from model_trial import initialize,card_for
  assert initialize()==NEW and card_for(B)==card
  arm['source_sha256']=NEW;arm['model_card_sha256']=hashlib.sha256(canonical(card)).hexdigest();arm['predecessor_arming_sha256']=hashlib.sha256(previous).hexdigest();arm['revision']=5;arm['source_correction']='exact-accepted-xe-vram0-counter-format';arm['verified_epoch']=int(time.time())
  newreceipt=ROOT/'arming-receipts'/(B+'-model-revision5.json');assert not newreceipt.exists();replace(newreceipt,canonical(arm))
  replace(journal,canonical({'state':'complete','old':OLD,'new':NEW,'booking_id':B,'arming_sha256':hashlib.sha256(canonical(arm)).hexdigest()}))
  print(json.dumps({'state':'updated-and-reverified','booking_id':B,'source_sha256':NEW,'arming_receipt':str(newreceipt),'arming_sha256':hashlib.sha256(canonical(arm)).hexdigest(),'timers_unchanged':True,'no_stack_effect':True},sort_keys=True))
 except BaseException:
  for n,p in paths.items():replace(p,oldbytes[n])
  assert all(protected_bytes(p,executable=n.endswith('.py'),maximum=262144)==oldbytes[n] for n,p in paths.items())
  replace(journal,canonical({'state':'rolled-back','old':OLD,'new':NEW,'booking_id':B}));raise
'''
out='OLD='+repr(old)+'\nNEW='+repr(new)+'\nFILES='+repr(files)+'\n'+code
Path('/private/tmp/b60-model-trial-vram0-update.py').write_text(out)
print(json.dumps({'updater_sha256':hashlib.sha256(out.encode()).hexdigest(),'old':old,'new':new},sort_keys=True))
