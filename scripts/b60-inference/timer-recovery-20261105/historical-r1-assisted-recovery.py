"""One exact-booking assisted recovery, never qualification or experiment success."""
import json,os,sys,time,hashlib,subprocess
from pathlib import Path
B='b60-exclusive-20261105-day-r1'
ROOT=Path('/var/lib/local-ai-lab')
sys.path.insert(0,'/usr/local/libexec/local-ai-lease/exclusive-session')
from lab_hours_exclusive_cli import context
from lab_hours_exclusive_session import ExclusiveSession,canonical

def command(args,timeout=30):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError('RECOVERY_FIXED_COMMAND_FAILED')
    return p.stdout

def scope_inactive(unit):
    raw=command(['systemctl','show',unit,'--property=ActiveState,MainPID,TasksCurrent'])
    v=dict(line.split('=',1) for line in raw.splitlines())
    return v['ActiveState'] in {'inactive','failed'} and v['MainPID']=='0' and v.get('TasksCurrent') in {'0','','[not set]'}

# Source-local code; emits no configuration, credentials, argv or document bytes.
PAPERLESS=r'''
import pathlib,subprocess,time,json,os
unit='paperless-summary.timer';service='paperless-summary.service'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,check=True,timeout=30);return p.stdout.strip()
def prop(unit,key):return run(['systemctl','show',unit,'--property='+key,'--value'])
assert prop(unit,'ActiveState')=='inactive' and prop(unit,'UnitFileState')=='enabled'
assert prop(service,'ActiveState')=='inactive' and prop(service,'MainPID')=='0'
assert prop(unit,'Persistent')=='no' and not prop(unit,'TimersCalendar')
raw=prop(unit,'TimersMonotonic').splitlines()
assert len(raw)==2 and any('OnBootUSec=2min' in s for s in raw) and any('OnUnitInactiveUSec=5min' in s for s in raw)
parent=pathlib.Path('/run/systemd/system/paperless-summary.service.d')
created=not parent.exists();parent.mkdir(mode=0o755,exist_ok=True)
assert parent.is_dir() and not parent.is_symlink() and parent.stat().st_uid==0
p=parent/'90-b60-exclusive-20261105-day-r1-no-replay.conf'
fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'w') as f:
 f.write('[Service]\nExecCondition=\nExecCondition=/usr/bin/false\n');f.flush();os.fsync(f.fileno())
run(['systemctl','daemon-reload'])
run(['systemctl','start',unit])
limit=time.monotonic()+15
while prop(service,'Result')!='exec-condition' or prop(service,'ActiveState')!='inactive':
 if time.monotonic()>limit:raise RuntimeError('FIRST_POLL_NOT_SAFELY_SKIPPED_GATE_RETAINED')
 time.sleep(.2)
assert prop(service,'MainPID')=='0'
# A false ExecCondition means ExecStart (the document worker) did not execute.
p.unlink()
if created:parent.rmdir()
run(['systemctl','daemon-reload'])
value=run(['busctl','get-property','org.freedesktop.systemd1','/org/freedesktop/systemd1/unit/paperless_2dsummary_2etimer','org.freedesktop.systemd1.Timer','NextElapseUSecMonotonic'])
kind,raw=value.split();remaining=int(raw)/1000000-time.monotonic()
assert kind=='t' and 0<remaining<=301
assert prop(unit,'ActiveState')=='active' and prop(unit,'SubState')=='waiting'
assert prop(service,'MainPID')=='0' and prop(service,'ActiveState')=='inactive'
assert str(p) not in prop(service,'DropInPaths') and not p.exists()
print(json.dumps({'state':'monotonic-resumed','overdue_worker_skipped':True,'job_success_claimed':False,'temporary_gate_removed':True,'next_interval_remaining_seconds':remaining}))
'''
CALENDAR=r'''
import subprocess,json,sys
def run(args):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
unit=sys.argv[1]
assert unit in {'news-aggregator-ingest.timer','news-aggregator-digest.timer','epub-narration-monitor.timer'}
def prop(k):return run(['systemctl','show',unit,'--property='+k,'--value'])
assert prop('ActiveState')=='inactive' and prop('UnitFileState')=='enabled'
assert prop('Persistent') in {'yes','no'} and prop('TimersCalendar') and not prop('TimersMonotonic')
if prop('Persistent')=='yes':run(['systemctl','clean','--what=state',unit])
run(['systemctl','start',unit])
assert prop('ActiveState')=='active' and prop('SubState')=='waiting'
print(json.dumps({'state':'calendar-resumed','unit':unit,'skip_missed_calendar_events':True,'job_success_claimed':False}))
'''

def main():
    assert os.geteuid()==0 and os.uname().nodename=='proxmox'
    for kind in ['owner','guardian']:
        assert scope_inactive('b60-exclusive-'+kind+'-'+B+'.service')
    profile,store,bookings,scopes,adapter=context(B)
    fd=store.lock()
    try:
        state=store.read('session.json');assert state['phase']=='restoring' and state['booking_id']==B
        assert time.time()+300<state['restore_deadline']
        entry=store.read('entry.json');assert hashlib.sha256(canonical(entry)).hexdigest()==state['entry_sha256']
        adapter._load() # Exact claimed binding, shared markers and exclusion are checked.
        assert bookings.get(B)['state']=='claimed'
        for guest in profile['guest_plans']:
            assert adapter._guest(guest,'verify',state['restore_deadline']).get('verified') is True
        missing={('114','news-aggregator-digest.timer'),('114','news-aggregator-ingest.timer'),('115','paperless-summary.timer'),('116','epub-narration-monitor.timer')}
        for row in adapter.private['units']:
            now=adapter.units.observe(row['guest'],row['unit'],state['restore_deadline'])
            assert now['UnitFileState']==row['enablement']
            assert now['ActiveState']==('inactive' if (row['guest'],row['unit']) in missing else row['active'])
        store.write('manual-recovery.json',{'schema':'b60-assisted-recovery.v1','booking_id':B,'reason':'CALENDAR_EMPTY_PROPERTY_AND_MONOTONIC_POLICY_GAP','started_epoch':int(time.time()),'qualification_passed':False},immutable=True)
        state['trial_failed']=True
        state['manual_assistance_required']=True
        store.write('session.json',state)
        # Remove only exact runtime /dev/null masks for entry rows that were
        # not runtime-masked; service starts/stops are not part of this step.
        mask_check="import pathlib,sys,json; p=pathlib.Path('/run/systemd/system')/sys.argv[1]; print(json.dumps({'masked':p.is_symlink() and str(p.readlink())=='/dev/null'}))"
        cleared=[]
        for row in adapter.private['units']:
            if row['enablement']=='masked-runtime': continue
            value=json.loads(command(['pct','exec',row['guest'],'--','python3','-B','-c',mask_check,row['unit']]))
            if value['masked']:
                command(['pct','exec',row['guest'],'--','systemctl','unmask','--runtime',row['unit']])
                cleared.append({'guest':row['guest'],'unit':row['unit']})
        proof=[{'runtime_masks_cleared':cleared}]
        proof.append(json.loads(command(['pct','exec','115','--','python3','-B','-c',PAPERLESS])))
        for guest,unit in [('114','news-aggregator-digest.timer'),('114','news-aggregator-ingest.timer'),('116','epub-narration-monitor.timer')]:
            proof.append(json.loads(command(['pct','exec',guest,'--','python3','-B','-c',CALENDAR,unit])))
        # Confirm temporary configuration has disappeared and actual plan inventory matches.
        check="import sys,json;sys.path.insert(0,'/usr/local/libexec/local-ai-lease/entry-checkpoint');from lab_hours_guest_checkpoint import private_json;from lab_hours_prepare_entry_plan import current_plan;from pathlib import Path;assert private_json(Path(sys.argv[1]))==current_plan(sys.argv[2]);print('matched')"
        for guest in profile['guest_plans']:
            assert command(['pct','exec',guest,'--','python3','-B','-c',check,'/var/lib/local-ai-lab-entry/'+B+'/plan.json',guest]).strip()=='matched'
        assert adapter.verify_entry(entry) is True
        state['production_restored']=True;state['deadline_missed']=time.time()>=state['restore_deadline']
        assert state['deadline_missed'] is False
        session=ExclusiveSession(store,adapter);session._phase(state,'restored')
        assert adapter.release(state) is True # Existing exact-binding release, fresh full verification.
        session._phase(state,'released')
        store.write('manual-recovery-terminal.json',{'schema':'b60-assisted-recovery-result.v1','booking_id':B,'state':'failed-qualified-trial-restored-with-assistance','production_restored':True,'qualification_passed':False,'finished_epoch':int(time.time()),'timer_proof':proof},immutable=True)
        print(json.dumps({'state':'restored-and-released-with-assistance','qualification_passed':False,'production_restored':True,'booking_id':B}))
    finally:
        os.close(fd);adapter.boundary.close()

if __name__=='__main__':main()
