"""Accept completed restore proof while permitting only verified future timer work.
No model, service, timer, configuration or lease effect is performed.
"""
import copy,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path('/var/lib/local-ai-lab');BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');PACKAGE=BASE.parent/'post-xe-qualification-20261106-r5'
B='b60-exclusive-20261106-day-r5';INCIDENT='b60-xe-20261106-1794002063';OPEN_SHA='7c1355adec390764cd970036233c1a70325d224b387e751dff4ef06db0e5cc6e'
REVIEW_SHA='47238d1b6369210edb0e1d28e69929f308c70e8967c452c4b788f441ebe88539'
sys.path[:0]=[str(PACKAGE),str(BASE)]
from qualification import context,initialize,kernel,canon
from lab_hours_exclusive_profile import protected_bytes
from host_exclusion import host_exclusion
from lab_hours_exclusive_admission import TRIGGERS
from full_inference_lab_runtime import _gpu_users

def require(v,code):
 if v is not True:raise RuntimeError(code)
def command(a,timeout=15):
 p=subprocess.run(a,capture_output=True,text=True,timeout=timeout);require(p.returncode==0,'FIXED_METADATA_FAILED');return p.stdout.strip()
def object_path(unit):return '/org/freedesktop/systemd1/unit/'+''.join(c if c.isalnum() else '_'+format(ord(c),'02x') for c in unit)
def number(guest,unit,interface,prop):
 kind,value=command(['pct','exec',guest,'--','busctl','get-property','org.freedesktop.systemd1',object_path(unit),'org.freedesktop.systemd1.'+interface,prop]).split();require(kind=='t' and value.isdigit(),'NUMERIC_CLOCK_PROPERTY');return int(value)
def clocks(guest=None):
 code="import time,json;from pathlib import Path;print(json.dumps({'realtime':time.time(),'monotonic':time.monotonic(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}))"
 started=time.time();value=json.loads(command((['pct','exec',guest,'--'] if guest else [])+['python3','-B','-c',code]));value['host_request_started']=started;value['host_request_finished']=time.time();return value
def finite_future(n,now):return type(n) is int and 0<n<18446744073709551615 and n/1e6>now

def validate_progress(entry,current,timer,*,finished,observed):
 """Pure, closed predicate for a timer-owned oneshot after full restoration."""
 require(entry['active']=='inactive' and entry['enablement']=='static','ONLY_INACTIVE_ONESHOT_PROGRESS')
 require(current.get('ActiveState') in {'active','activating'} and current.get('MainPID','').isdigit() and int(current['MainPID'])>0,'RUNNING_SERVICE_IDENTITY')
 require(current.get('UnitFileState')==entry['enablement'],'SERVICE_ENABLEMENT_DRIFT')
 require(timer['active']=='active' and timer['substate']=='running' and timer['trigger']==entry['unit'],'EXACT_TIMER_SERVICE_BINDING')
 last=timer['last_usec'];start=timer['service_start_usec']
 require(type(last) is int and type(start) is int and 0<last<18446744073709551615 and 0<start<18446744073709551615,'FINITE_TRIGGER_TIMES')
 require(last/1e6>max(finished,observed) and start/1e6>max(finished,observed) and abs(start-last)<=2_000_000,'FUTURE_TIMER_NOT_CATCHUP')
 return True

def create(p,raw):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)

def accept():
 require(hashlib.sha256(REVIEW_BYTES).hexdigest()==REVIEW_SHA,'EXACT_INDEPENDENT_ACTUAL_REVIEW')
 review=json.loads(REVIEW_BYTES);post=copy.deepcopy(review['result'])
 require(post['schema']=='b60-post-xe-independent-postcheck.v1' and post['booking_id']==B,'HISTORICAL_PROOF_IDENTITY')
 require(post['production_restored'] is True and post['unit_states_match_entry'] is True and post['all_five_checkpoint_verifications']=={g:True for g in ('104','110','114','115','116')},'ACTUAL_RESTORATION_PROOF')
 require(post['trial_failed'] is False and post['manual_assistance_required'] is False and post['deadline_missed'] is False and post['qualification_terminal']['qualified'] is True and post['answers']['state']=='passed','ACTUAL_QUALIFICATION_PROOF')
 with host_exclusion(ROOT):
  require(not any((ROOT/n).exists() or (ROOT/n).is_symlink() for n in ('lease.json','lease.lock','full-inference-drain.json','full-inference-drain.lock')) and not Path('/run/local-ai-lab-operation.lock').exists(),'SHARED_EXCLUSION_NOT_RELEASED')
  require(json.loads(command(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'},'SHARED_NOT_READY')
  profile,store,bookings,scopes,adapter=context(B)
  require(not any(v.get('state')=='claimed' for v in bookings.list()),'OTHER_BOOKING_CLAIMED')
  raw=command(['systemctl','list-units','--all','--no-legend','--plain','aster-local-ai-pilot-owner-*','aster-local-ai-pilot-guardian-*','b60-exclusive-owner-*','b60-exclusive-guardian-*'])
  require(not any(len(l.split())>3 and l.split()[2] in {'active','activating','deactivating'} for l in raw.splitlines()),'OTHER_OWNER_ACTIVE')
  require(initialize()==post['source_sha256'],'QUALIFICATION_SOURCE_DRIFT')
  for n,sha in post['record_sha256'].items():require(hashlib.sha256(protected_bytes(ROOT/n,maximum=262144)).hexdigest()==sha,'IMMUTABLE_PROOF_DRIFT')
  state=store.read('session.json');require(state['phase']=='released' and state['production_restored'] is True and state['trial_failed'] is False,'SESSION_NOT_COMPLETE')
  adapter.private=store.read('adapter.json');deadline=time.time()+480
  arm=json.loads(protected_bytes(ROOT/'arming-receipts'/(B+'-post-xe.json')))
  profile_sha=hashlib.sha256(protected_bytes(ROOT/'exclusive-activations'/(B+'.json'))).hexdigest();require(profile_sha==arm['profile_sha256'],'EXACT_ACTIVATION_PROFILE')
  plan_hashes={}
  for g,sha in profile['guest_plans'].items():
   actual=command(['pct','exec',g,'--','sha256sum','/var/lib/local-ai-lab-entry/'+B+'/plan.json']).split()[0];require(actual==sha,'EXACT_GUEST_PLAN');plan_hashes[g]=actual
  require(adapter._mount_identity(deadline)==adapter.private['mount_identity'],'MOUNT_DRIFT')
  # Reverify source-local configuration and immutable runtime/model bytes, with
  # no assumption that correctly resumed periodic jobs must remain idle.
  guests={g:adapter._guest(g,'verify',deadline).get('verified') is True for g in profile['guest_plans']}
  require(all(guests.values()),'CURRENT_CHECKPOINT_DRIFT')
  clock_view={g:clocks(g) for g in ('104','110','114','115','116')};clock_view['host']=clocks()
  for g,v in clock_view.items():
   require(v['realtime']-v['monotonic']<1794008400 and v['host_request_started']-2<=v['realtime']<=v['host_request_finished']+2,'BOOT_OR_WALL_CLOCK_DISCONTINUITY')
   old=next((x['guest_clock'] for name,x in post['scheduled_work_restored'].items() if name.startswith(g+'/') and x.get('guest_clock')),None)
   if old:require(v['monotonic']>=old['monotonic'] and abs((v['realtime']-v['monotonic'])-(old['realtime']-old['monotonic']))<2,'MONOTONIC_CLOCK_DISCONTINUITY')
  progress=[];timers={};current={}
  for row in adapter.private['units']:
   g,u=row['guest'],row['unit'];current[(g,u)]=adapter.units.observe(g,u,deadline)
  for row in adapter.private['units']:
   g,u=row['guest'],row['unit'];v=current[(g,u)]
   require(v['UnitFileState']==row['enablement'],'CURRENT_ENABLEMENT_DRIFT')
   if u.endswith('.timer'):
    require(v['ActiveState']==row['active'],'TIMER_ACTIVE_STATE_DRIFT')
    if row['active']!='active':continue
    sub=command(['pct','exec',g,'--','systemctl','show',u,'--property=SubState','--value'])
    trigger=command(['pct','exec',g,'--','systemctl','show',u,'--property=Triggers','--value']);require(TRIGGERS.get(g,{}).get(u)==trigger,'FIXED_TIMER_BINDING')
    current[(g,trigger)]=adapter.units.observe(g,trigger,deadline)
    t={'active':v['ActiveState'],'substate':sub,'trigger':trigger,'last_usec':number(g,u,'Timer','LastTriggerUSec'),'service_start_usec':number(g,trigger,'Service','ExecMainStartTimestamp')}
    if sub=='waiting':
     real=number(g,u,'Timer','NextElapseUSecRealtime');mono=number(g,u,'Timer','NextElapseUSecMonotonic');now=clocks(g)
     require(finite_future(real,now['realtime']) or finite_future(mono,now['monotonic']),'FUTURE_TIMER_UNPROVEN')
     t.update(next_realtime_usec=real,next_monotonic_usec=mono)
    elif sub=='running':
     service=next(x for x in adapter.private['units'] if x['guest']==g and x['unit']==trigger)
     validate_progress(service,current[(g,trigger)],t,finished=post['finished_epoch'],observed=post['observed_epoch']);progress.append({'guest':g,'unit':trigger,**t})
    else:raise RuntimeError('UNSUPPORTED_TIMER_SUBSTATE')
    timers[(g,u)]=t
  for row in adapter.private['units']:
   g,u=row['guest'],row['unit'];v=current[(g,u)]
   if u.endswith('.timer') or v['ActiveState']==row['active']:continue
   if row['enablement']=='static' and row['active']=='activating' and v['ActiveState'] in {'active','activating'} and v.get('MainPID','').isdigit() and int(v['MainPID'])>0:continue
   trigger=next((t for (owner,t),s in ((key,value['trigger']) for key,value in timers.items()) if owner==g and s==u),None)
   require(trigger is not None,'UNEXPLAINED_UNIT_STATE_DRIFT')
   validate_progress(row,v,timers[(g,trigger)],finished=post['finished_epoch'],observed=post['observed_epoch'])
  holders=_gpu_users();require(len(holders)==1 and next(iter(holders)).cgroup.endswith('/lxc/110/ns/system.slice/aster-llama.service'),'ACCEPTED_DRM_HOLDER')
  command(['pct','exec','110','--','/usr/local/sbin/aster-llama-production-auth-probe'],30)
  require(command(['pct','exec','115','--','python3','-B','-c',"from pathlib import Path;print(len(list(Path('/run/systemd/system/paperless-summary.service.d').glob('90-b60-no-replay-*.conf'))))"])=='0','TEMPORARY_GATE_REMAINS')
  post['historical_independent_postcheck_sha256']=REVIEW_SHA;post['current_checkpoint_verifications']=guests;post['current_profile_sha256']=profile_sha;post['current_guest_plan_sha256']=plan_hashes;post['current_scheduled_progress']=progress
  post['current_timer_observations']={g+'/'+u:v for (g,u),v in timers.items()};post['current_observed_epoch']=int(time.time());post['clock_continuity']=clock_view
  post['postcheck_kernel']=post['kernel'];post['kernel']=kernel(adapter,time.time()+5,1794002064)
  parent=ROOT/'device-incidents'/INCIDENT;require(hashlib.sha256(protected_bytes(parent/'open.json')).hexdigest()==OPEN_SHA,'ORIGINAL_INCIDENT_DRIFT')
  require(all(not (parent/n).exists() for n in ('acceptance-source.py','postcheck.json','independent-postcheck-acceptance.json','closure.json')),'PRIOR_ACCEPTANCE_EXISTS')
  for n,sha in post['record_sha256'].items():require(hashlib.sha256(protected_bytes(ROOT/n,maximum=262144)).hexdigest()==sha,'FINAL_IMMUTABLE_PROOF_DRIFT')
  require(hashlib.sha256(SOURCE_BYTES).hexdigest()==SOURCE_SHA256,'ACCEPTANCE_SOURCE_IDENTITY')
  create(parent/'acceptance-source.py',SOURCE_BYTES);create(parent/'independent-postcheck-acceptance.json',REVIEW_BYTES)
  raw=canon(post);create(parent/'postcheck.json',raw)
  closure={'schema':'b60-device-incident-closure.v1','state':'CLOSED_FOR_ACCEPTED_SYCL_CONTINUATION','incident_id':INCIDENT,'original_open_sha256':OPEN_SHA,'qualification_booking_id':B,'postcheck_sha256':hashlib.sha256(raw).hexdigest(),'accepted_epoch':int(time.time()),'acceptance_source_sha256':SOURCE_SHA256}
  create(parent/'closure.json',canon(closure));print(json.dumps({'closure':closure,'postcheck':post,'closure_sha256':hashlib.sha256(canon(closure)).hexdigest()},sort_keys=True))
if __name__=='__main__':accept()
