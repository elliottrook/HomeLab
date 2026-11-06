import sys,time,json,hashlib
from pathlib import Path
R=Path('/var/lib/local-ai-lab');P=Path('/usr/local/libexec/local-ai-lease/exclusive-session');B='b60-exclusive-20261105-day-r3';sys.path.insert(0,str(P))
from host_exclusion import host_exclusion
from lab_hours_exclusive_cli import context
from lab_hours_exclusive_session import canonical
from lab_hours_exclusive_profile import protected_bytes
with host_exclusion(R):
 assert not any(p.exists() for p in [R/'lease.json',R/'lease.lock',R/'full-inference-drain.json',R/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
 profile,store,bookings,scopes,adapter=context(B)
 state=store.read('session.json');entry=store.read('entry.json');adapter.private=store.read('adapter.json');row=bookings.get(B)
 assert state['phase']=='released' and state['production_restored'] is True and state['trial_failed'] is False and state['deadline_missed'] is False and state.get('manual_assistance_required',False) is False
 assert row['state']=='complete' and row['result_code']=='RESTORED' and row['finished_epoch']<row['end_epoch']
 assert hashlib.sha256(canonical(entry)).hexdigest()==state['entry_sha256']==row['entry_sha256']
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in P.glob('*.py')}
 assert hashlib.sha256(canonical(pins)).hexdigest()=='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2' and profile['source_sha256']==pins
 deadline=int(time.time())+480
 mount=adapter._mount_identity(deadline)==adapter.private['mount_identity'];units=adapter.units.verify(adapter.private['units'],deadline)
 guests={g:adapter._guest(g,'verify',deadline).get('verified') is True for g in profile['guest_plans']}
 assert mount and units and all(guests.values())
 paths=[store.root/n for n in ('admission.json','entry.json','session.json','adapter.json','unit-state-recovery.json')]+[R/'exclusive-releases'/(B+'.json'),R/'reservations/records'/(B+'.json'),R/'exclusive-integrity'/B/'terminal.json',R/'arming-receipts'/(B+'.json')]
 hashes={str(p.relative_to(R)):hashlib.sha256(protected_bytes(p,maximum=262144)).hexdigest() for p in paths if p.exists()}
 assert json.loads(protected_bytes(R/'exclusive-releases'/(B+'.json')))==adapter.private['binding']
 out={'schema':'b60-restore-only-postcheck.v1','booking_id':B,'observed_epoch':int(time.time()),'result':'normal-restore-only-pass','session':{k:state[k] for k in ('phase','production_restored','trial_failed','deadline_missed','updated_epoch','restore_deadline')},'manual_assistance_required':state.get('manual_assistance_required',False),'ledger':{k:row[k] for k in ('state','result_code','claimed_epoch','finished_epoch','start_epoch','end_epoch') if k in row},'entry_sha256':state['entry_sha256'],'mount_identity_matches':mount,'unit_states_match_entry':units,'guest_checkpoints_verify':guests,'source_map_sha256':hashlib.sha256(canonical(pins)).hexdigest(),'profile_sha256':hashlib.sha256(protected_bytes(R/'exclusive-activations'/(B+'.json'))).hexdigest(),'record_sha256':hashes,'unit_recovery_evidence_present':(store.root/'unit-state-recovery.json').exists(),'manual_recovery_evidence_present':any((store.root/n).exists() for n in ('manual-recovery.json','manual-recovery-terminal.json')),'model_experiment_scheduled':False,'new_health_or_generation_probe_executed':False}
 if out['unit_recovery_evidence_present']:
  v=store.read('unit-state-recovery.json');out['unit_recovery_events']=[{k:e[k] for k in ('guest','unit','prior_state','result','exit_code','signal','observed_epoch','state_reset','application_job_success_claimed') if k in e} for e in v['events']]
 print(json.dumps(out,sort_keys=True))

