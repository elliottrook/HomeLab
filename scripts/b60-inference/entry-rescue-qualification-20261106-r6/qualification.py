"""One fixed restore-only owner-loss-after-healthy-restart qualification.

No candidate model, inference request, download or package change is executed.
"""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');HERE=BASE.parent/'entry-rescue-qualification-20261106-r6';ROOT=Path('/var/lib/local-ai-lab')
FILES={'qualification.py','entry_recovery.py','fixed_command.py','backup_chain_history.py','guest_entry_scope.py'}
BASE_SHA='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2';B='b60-exclusive-20261106-day-r6';WORKLOAD='b60-entry-backend-preservation-qualification-v1'
def require(v,c):
 if v is not True:raise RuntimeError(c)
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def call(a,t=30):
 p=subprocess.run(a,capture_output=True,text=True,timeout=t);require(p.returncode==0,'FIXED_COMMAND_FAILED');return p.stdout.strip()
def initialize():
 require(os.geteuid()==0 and os.uname().nodename=='proxmox','HOST_IDENTITY');sys.path.insert(0,str(BASE))
 from lab_hours_exclusive_profile import protected_bytes
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')};require(len(pins)==30 and hashlib.sha256(canon(pins)).hexdigest()==BASE_SHA,'BASE_DRIFT')
 m=json.loads(protected_bytes(HERE/'manifest.json'));require(set(m)==FILES and {p.name for p in HERE.glob('*.py')}==FILES,'SOURCE_CLOSURE')
 for n,s in m.items():require(hashlib.sha256(protected_bytes(HERE/n,executable=True,maximum=262144)).hexdigest()==s,'SOURCE_DRIFT')
 return m
def kernel(a,d,since):
 import re
 raw=a._call(('journalctl','-k','--since','@'+str(int(since)),'--no-pager','-o','cat'),d,3)
 bad=any('out of memory' in l or 'oom-kill' in l or re.search(r'\bxe\b',l) and re.search(r'\b(?:reset\w*|hang\w*|hung|wedged|device lost|fault\w*|error\w*)\b',l) for l in raw.lower().splitlines());require(not bad,'NEW_KERNEL_HAZARD');return {'new_kernel_hazard_count':0,'since_epoch':int(since),'observed_epoch':int(time.time())}
def context(b):
 require(b==B,'FIXED_BOOKING');m=initialize()
 from lab_hours_exclusive_profile import protected_bytes
 from lab_hours_exclusive_cli import context as base_context
 card_raw=protected_bytes(ROOT/'entry-rescue-cards'/(b+'.json'));card=json.loads(card_raw)
 result=base_context(b);profile,store,bookings,scopes,a=result;row=bookings.get(b)
 require(card['schema']=='b60-entry-rescue-card.v1' and card['booking_id']==b and card['source_sha256']==m,'CARD_BINDING')
 require(row['workload']==WORKLOAD and row['owner']=='b60-stream-a' and row['kind']=='exclusive-stack' and all(row[k]==card[k] for k in ('start_epoch','end_epoch')) and profile['trial_seconds']==600 and profile['experiment'] is None,'FIXED_PROFILE')
 dispatch=json.loads(protected_bytes(ROOT/'exclusive-dispatch'/(b+'.json')));require(dispatch['card_sha256']==hashlib.sha256(card_raw).hexdigest(),'DISPATCH_BINDING')
 from backup_chain_history import backup
 a.admission.backup=lambda **kw:backup(a,store,card,**kw)
 original_admit=a.admission
 def admit(row,profile):
  require(not (store.root/'qualification-intent.json').exists(),'SPENT_ATTEMPT');require(original_admit(row,profile),'FRESH_ADMISSION')
  import importlib.util
  sp=importlib.util.spec_from_file_location('fixed_incident_gate',BASE.parent/'full-inference-pilot/b60_exclusive_card_bridge.py');gate=importlib.util.module_from_spec(sp);sp.loader.exec_module(gate)
  gate.require_incident_closed();store.write('qualification-kernel-before.json',kernel(a,row['end_epoch']-900,1794002064),immutable=True);return True
 a.admission=admit;a.arm=lambda state,profile:arm(b,scopes,state,store)
 original=a.runner
 def runner(command,timeout):
  command=tuple(command);prefix=('pct','exec','116','--','/usr/bin/python3','-B','/usr/local/libexec/local-ai-lease/entry-checkpoint/lab_hours_guest_checkpoint.py')
  if command[:7]==prefix:
   path=str(HERE/'guest_entry_scope.py');code,raw=original(('pct','exec','116','--','sha256sum',path),10);require(code==0 and raw.split()[0]==m['guest_entry_scope.py'],'WRAPPER_DRIFT');command=command[:6]+(path,'checkpoint')+command[7:]
  if command==('pct','exec','110','--','systemctl','start','aster-llama.service'):
   p=store.root/'entry-backend-start-intent.json'
   if p.exists():
    code,raw=original(('pct','exec','110','--','systemctl','is-active','aster-llama.service'),5);require(code==0 and raw.strip()=='active','ENTRY_START_ALREADY_ATTEMPTED')
    store.write('entry-backend-idempotent-start.json',{'booking_id':b,'observed_epoch':int(time.time()),'new_backend_start_invoked':False},immutable=True);return 0,''
   store.write(p.name,{'booking_id':b,'observed_epoch':int(time.time()),'maximum_start_attempts':1},immutable=True)
   code,raw=original(command,timeout);require(code==0,'FIRST_ENTRY_START_FAILED')
   if scopes._show().get('MainPID')==str(os.getpid()):
    until=min(time.time()+90,bookings.get(b)['end_epoch']-900)
    while time.time()<until:
     kernel(a,time.time()+5,row['start_epoch'])
     rc,_=original(('pct','exec','110','--','/usr/local/sbin/aster-llama-production-auth-probe'),10)
     if rc==0:break
     time.sleep(2)
    else:raise RuntimeError('FIRST_ENTRY_HEALTH_NOT_VERIFIED')
    require(a._guest('110','verify',bookings.get(b)['end_epoch']-900).get('verified') is True,'FIRST_ENTRY_ACTIVE_BINDING')
    store.write('qualification-owner-loss-intent.json',{'booking_id':b,'observed_epoch':int(time.time()),'exit_status':86,'after_first_accepted_start_and_health':True,'model_generation_calls':0},immutable=True)
    current=store.read('session.json');require(current['phase']=='restoring','FAULT_PHASE');current['trial_failed']=True;store.write('session.json',current)
    os._exit(86)
   return code,raw
  return original(command,timeout)
 a.runner=runner;a.units.runner=runner
 from entry_recovery import install
 from full_inference_lab_runtime import _gpu_users
 install(a,store,kernel_check=kernel,gpu_users=_gpu_users)
 def execute(state,deadline):
  store.write('qualification-intent.json',{'booking_id':b,'observed_epoch':int(time.time()),'purpose':'owner-loss-after-healthy-entry-restart','model_generation_calls':0},immutable=True);return True
 a.execute=execute;return result

def arm(b,scopes,state,store):
 remaining=int(state['restore_deadline']-time.time());require(remaining>900,'GUARDIAN_MARGIN')
 call(['systemd-run','--quiet','--unit='+scopes.guardian,'--property=Type=exec','--property=KillMode=control-group','--property=Restart=no','--property=RuntimeMaxSec='+str(remaining+600),'/usr/bin/python3','-B',str(HERE/'qualification.py'),'watch','--booking-id',b],15)
 v=dict(l.split('=',1) for l in call(['systemctl','show',scopes.guardian,'--property=ActiveState,MainPID']).splitlines());return v.get('ActiveState')=='active' and int(v.get('MainPID','0'))>0

def operate(action,b):
 profile,store,bookings,scopes,a=context(b)
 from lab_hours_exclusive_session import ExclusiveSession
 from lab_hours_exclusive_guardian import guard
 try:
  if action=='launch':
   row=bookings.get(b);now=int(time.time());require(row['state']=='reserved' and row['start_epoch']<=now<=row['start_epoch']+120,'LAUNCH_WINDOW')
   call(['systemd-run','--quiet','--unit='+scopes.owner,'--property=Type=exec','--property=KillMode=control-group','--property=Restart=no','--property=RuntimeMaxSec='+str(row['end_epoch']-now+300),'/usr/bin/python3','-B',str(HERE/'qualification.py'),'run','--booking-id',b],15);return {'state':'owner-launched'}
  if action=='watch':
   result=guard(store,a,owner=profile['owner'],owner_alive=scopes.alive,fence_owner=scopes.fence)
   state=store.read('session.json');require(state['phase']=='released' and state['production_restored'] is True and not state.get('manual_assistance_required',False) and state['deadline_missed'] is False,'RESTORATION_NOT_QUALIFIED')
   require((store.root/'qualification-owner-loss-intent.json').exists() and (store.root/'entry-backend-preservation-proof.json').exists(),'FAULT_OR_PRESERVATION_PROOF_MISSING')
   preserve=store.read('entry-backend-preservation-proof.json');require(a.units.observe('110','aster-llama.service',time.time()+15)['MainPID']==preserve['after']['main_pid'] and store.read('entry-backend-idempotent-start.json')['new_backend_start_invoked'] is False,'BACKEND_RESTART_NOT_EXCLUDED')
   owner=dict(l.split('=',1) for l in call(['systemctl','show',scopes.owner,'--property=ActiveState,MainPID,TasksCurrent,ExecMainCode,ExecMainStatus']).splitlines());require(owner.get('ActiveState')=='failed' and owner.get('MainPID')=='0' and owner.get('TasksCurrent') in {'0','','[not set]'} and owner.get('ExecMainCode')=='1' and owner.get('ExecMainStatus')=='86','ACTUAL_OWNER_EXIT86_REQUIRED')
   start=dict(l.split('=',1) for l in a._call(('pct','exec','110','--','systemctl','show','aster-llama.service','--property=ExecMainStartTimestampMonotonic'),time.time()+15,10).splitlines());require(int(start['ExecMainStartTimestampMonotonic'])==preserve['after']['exec_main_start_usec'],'BACKEND_START_IDENTITY_CHANGED')
   out={'schema':'b60-entry-preservation-terminal.v1','booking_id':b,'qualified':True,'owner_loss_after_first_healthy_start':True,'accepted_backend_preserved':True,'additional_backend_start_calls':0,'model_generation_calls':0,'manual_assistance_required':False,'finished_epoch':int(time.time()),'source_sha256':initialize(),'kernel_after':kernel(a,time.time()+10,bookings.get(b)['start_epoch']),'all_crash_windows_qualified':False}
   store.write('qualification-terminal.json',out,immutable=True);return out
  require(action=='run' and scopes._show().get('MainPID')==str(os.getpid()),'OWNER_IDENTITY');s=ExclusiveSession(store,a);s.begin(bookings.get(b),owner=profile['owner'],trial_seconds=600);return s.run_trial(owner=profile['owner'])
 finally:a.boundary.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=('launch','run','watch'));p.add_argument('--booking-id',required=True);args=p.parse_args()
 try:print(json.dumps(operate(args.action,args.booking_id),sort_keys=True))
 except Exception as e:print(json.dumps({'state':'no_go','failure_type':type(e).__name__,'code':str(e) if type(e) is RuntimeError and str(e).replace('_','').isalnum() else 'UNCLASSIFIED'}));raise SystemExit(1)
