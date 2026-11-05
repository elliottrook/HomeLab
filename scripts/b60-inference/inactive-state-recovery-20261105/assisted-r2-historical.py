"""Exact R2 assisted recovery; a failed qualification can never become a pass."""
import os,sys,json,time,hashlib,subprocess
from pathlib import Path
B='b60-exclusive-20261105-day-r2';ROOT=Path('/var/lib/local-ai-lab')
sys.path.insert(0,'/usr/local/libexec/local-ai-lease/exclusive-session')
from lab_hours_exclusive_cli import context
from lab_hours_exclusive_session import ExclusiveSession,canonical

def run(a):
    p=subprocess.run(a,capture_output=True,text=True,timeout=30)
    if p.returncode:raise RuntimeError('ASSISTED_RECOVERY_FIXED_COMMAND_FAILED')
    return p.stdout

def main():
    assert os.geteuid()==0 and os.uname().nodename=='proxmox'
    profile,store,bookings,scopes,adapter=context(B)
    assert scopes.fence({}) is True # Idempotently proves exact owner absent/empty.
    raw=run(['systemctl','show',scopes.guardian,'--property=ActiveState,MainPID,TasksCurrent'])
    guard=dict(l.split('=',1) for l in raw.splitlines());assert guard['ActiveState'] in {'failed','inactive'} and guard['MainPID']=='0' and guard.get('TasksCurrent') in {'0','','[not set]'}
    fd=store.lock()
    try:
        state=store.read('session.json');assert state['phase']=='restoring' and state['booking_id']==B and time.time()+300<state['restore_deadline']
        entry=store.read('entry.json');assert hashlib.sha256(canonical(entry)).hexdigest()==state['entry_sha256']
        adapter._load();assert bookings.get(B)['state']=='claimed'
        rows=adapter.private['units'];target=[r for r in rows if (r['guest'],r['unit'])==('114','news-aggregator-ingest.service')][0]
        current=adapter.units.observe('114',target['unit'],state['restore_deadline'])
        assert target['active']=='inactive' and target['enablement']=='static' and current['ActiveState']=='failed' and current['MainPID']=='0' and current['TasksCurrent'] in {'0','','[not set]'}
        store.write('manual-recovery.json',{'schema':'b60-assisted-recovery.v1','booking_id':B,'reason':'QUIESCENT_FAILED_NEWS_SERVICE_NOT_RESET_TO_ENTRY_INACTIVE','started_epoch':int(time.time()),'qualification_passed':False,'application_job_success_claimed':False},immutable=True)
        state['trial_failed']=True;state['manual_assistance_required']=True;store.write('session.json',state)
        # Pause only the already-resumed Paperless timer during long entry hashing;
        # its exact installed policy rearms a future interval without catch-up.
        timer=[r for r in rows if (r['guest'],r['unit'])==('115','paperless-summary.timer')][0]
        service=[r for r in rows if (r['guest'],r['unit'])==('115','paperless-summary.service')][0]
        assert timer['active']=='active' and service['active']=='inactive'
        adapter.units.effect(timer,('stop',),state['restore_deadline'])
        obs=adapter.units.observe('115',service['unit'],state['restore_deadline'])
        if obs['ActiveState'] in {'active','activating'}:
            adapter.units.effect(service,('stop',),state['restore_deadline'])
        failures=[]
        for row in [target,service]:
            obs=adapter.units.observe(row['guest'],row['unit'],state['restore_deadline'])
            if obs['ActiveState']=='failed':
                assert obs['MainPID']=='0' and obs['TasksCurrent'] in {'0','','[not set]'}
                failures.append({'guest':row['guest'],'unit':row['unit'],'prior_state':'failed','application_job_success_claimed':False})
                adapter.units.effect(row,('reset-failed',),state['restore_deadline'])
            assert adapter.units.observe(row['guest'],row['unit'],state['restore_deadline'])['ActiveState']=='inactive'
        for guest in profile['guest_plans']:
            assert adapter._guest(guest,'verify',state['restore_deadline']).get('verified') is True
        assert adapter.timers(timer,state['restore_deadline']) is True
        adapter.units.effect(timer,('start',),state['restore_deadline'])
        assert adapter.verify_entry(entry) is True
        state['production_restored']=True;state['deadline_missed']=time.time()>=state['restore_deadline'];assert state['deadline_missed'] is False
        session=ExclusiveSession(store,adapter);session._phase(state,'restored')
        assert adapter.release(state) is True
        session._phase(state,'released')
        store.write('manual-recovery-terminal.json',{'schema':'b60-assisted-recovery-result.v1','booking_id':B,'state':'failed-qualification-restored-with-assistance','production_restored':True,'qualification_passed':False,'finished_epoch':int(time.time()),'cleared_unit_failures':failures,'application_job_success_claimed':False},immutable=True)
        print(json.dumps({'state':'R2-restored-and-released-with-assistance','qualification_passed':False,'production_restored':True}))
    finally:
        os.close(fd);adapter.boundary.close()

if __name__=='__main__':main()
