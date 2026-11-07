"""Reviewable immutable acceptance producer, invoked only after actual R7 release.

The calling builder must inject exact independent bytes, reviewed producer and
reconciler hashes and source pins. No placeholder input can create acceptance.
No model, restoration, timer, lease claim or device action is implemented here.
"""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path

BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session')
ROOT=Path('/var/lib/local-ai-lab');B='b60-exclusive-20261106-day-r7'
sys.path.insert(0,str(BASE))
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes
from lab_hours_exclusive_session import canonical
from lab_hours_reservations import ReservationStore

def create(path,raw):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)

def validate(post):
    assert post['schema']=='b60-entry-rescue-independent-postcheck.v1' and post['booking_id']==B
    for k in ('production_restored','unit_states_match_entry','persistent_mount_identity_matches','candidate_scope_empty','client_scope_empty','intended_fault_observed'):
        assert post[k] is True
    for k in ('manual_assistance_required','deadline_missed','all_crash_windows_qualified'):
        assert post[k] is False
    assert post['owner_exit_status']==86 and post['generation_count_scope']=='qualification-owned API requests only'
    assert post['model_generation_calls']==post['additional_backend_start_calls']==post['temporary_deny_gates']==0
    assert post['all_five_checkpoint_verifications']=={g:True for g in ('104','110','114','115','116')}
    assert post['booking_state']=='failed' and post['booking_result_code']=='FAILED_RESTORED' and post['trial_failed'] is True
    assert post['source_sha256']==SOURCE_SHA256 and len(SOURCE_SHA256)==4
    assert post['kernel']['new_kernel_hazard_count']==0 and post['kernel']['observed_epoch']>=post['finished_epoch']
    assert post['qualification_terminal']['qualified'] is True

def call(args,timeout=30):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    assert p.returncode==0
    return p.stdout.strip()

assert hashlib.sha256(PRODUCER_SOURCE).hexdigest()==PRODUCER_SHA256
assert hashlib.sha256(PRODUCER_REVIEW_BYTES).hexdigest()==PRODUCER_REVIEW_SHA256
assert len(PRODUCER_REVIEW_BYTES)>2
assert hashlib.sha256(INDEPENDENT_BYTES).hexdigest()==INDEPENDENT_SHA256
assert hashlib.sha256(RECONCILER_SOURCE).hexdigest()==RECONCILER_SHA256
assert all(isinstance(v,str) and len(v)==64 for v in (PRODUCER_SHA256,PRODUCER_REVIEW_SHA256,INDEPENDENT_SHA256,RECONCILER_SHA256))
independent=json.loads(INDEPENDENT_BYTES);independent=independent.get('result',independent)
validate(independent)
# This subprocess owns its own read-only host lock. Never nest its flock in ours.
p=subprocess.run(['/usr/bin/python3','-B','-'],input=RECONCILER_SOURCE,capture_output=True,timeout=480)
assert p.returncode==0
current=json.loads(p.stdout);validate(current)
assert current['record_sha256']==independent['record_sha256']
assert current['entry_sha256']==independent['entry_sha256']
assert current['guest_plan_sha256']==independent['guest_plan_sha256']
with host_exclusion(ROOT):
    assert time.time()-current['observed_epoch']<=60
    assert not any((ROOT/n).exists() or (ROOT/n).is_symlink() for n in ('lease.json','lease.lock','full-inference-drain.json','full-inference-drain.lock'))
    assert not Path('/run/local-ai-lab-operation.lock').exists()
    assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
    assert not any(v.get('state')=='claimed' for v in ReservationStore(ROOT/'reservations',expected_uid=0).list())
    raw=call(['systemctl','list-units','--all','--no-legend','--plain','aster-local-ai-pilot-owner-*','aster-local-ai-pilot-guardian-*','b60-exclusive-owner-*','b60-exclusive-guardian-*'])
    assert not any(len(l.split())>3 and l.split()[2] in {'active','activating','deactivating'} for l in raw.splitlines())
    hashes=current['record_sha256'];assert 15<=len(hashes)<=64
    allowed={f'exclusive-sessions/{B}/{n}' for n in ('admission.json','backup-history-admission.json','entry.json','adapter.json','session.json','qualification-intent.json','qualification-owner-loss-intent.json','entry-backend-start-intent.json','entry-backend-preservation-intent.json','entry-backend-preservation-proof.json','entry-backend-idempotent-start.json','qualification-kernel-before.json','qualification-terminal.json','unit-state-recovery.json')}
    allowed|={f'{folder}/{B}{suffix}' for folder,suffix in (('exclusive-dispatch','.json'),('exclusive-activations','.json'),('exclusive-releases','.json'),('reservations/records','.json'),('arming-receipts','-entry-rescue.json'),('entry-rescue-cards','.json'),('backup-chain-history','.json'))}
    optional={f'exclusive-sessions/{B}/unit-state-recovery.json'}
    assert allowed-optional<=set(hashes)<=allowed
    for path,sha in hashes.items():assert hashlib.sha256(protected_bytes(ROOT/path,maximum=262144)).hexdigest()==sha
    package=BASE.parent/'entry-rescue-qualification-20261106-r7'
    for name,sha in SOURCE_SHA256.items():assert hashlib.sha256(protected_bytes(package/name,executable=True,maximum=262144)).hexdigest()==sha
    pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')}
    assert len(pins)==30 and hashlib.sha256(canonical(pins)).hexdigest()=='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
    sys.path.insert(0,str(package));from qualification import kernel
    class ReadOnlyAdapter:
        def _call(self,args,deadline,maximum=120):
            assert time.time()<deadline
            return call(list(args),min(maximum,deadline-time.time()))
    final_kernel=kernel(ReadOnlyAdapter(),time.time()+10,1794002064)
    parent=ROOT/'controller-qualifications';parent.mkdir(mode=0o700,exist_ok=True)
    dest=parent/B;assert not dest.exists();dest.mkdir(mode=0o700)
    create(dest/'producer.py',PRODUCER_SOURCE)
    create(dest/'producer-review.json',PRODUCER_REVIEW_BYTES)
    create(dest/'independent-postcheck.json',INDEPENDENT_BYTES)
    create(dest/'current-postcheck.json',canonical(current))
    acceptance={'schema':'b60-entry-preservation-acceptance.v1','booking_id':B,'qualified':True,'accepted_epoch':int(time.time()),'scope':'owner-loss-after-first-healthy-entry-restart-only','all_crash_windows_qualified':False,'source_sha256':SOURCE_SHA256,'independent_postcheck_sha256':INDEPENDENT_SHA256,'current_postcheck_sha256':hashlib.sha256(canonical(current)).hexdigest(),'producer_sha256':PRODUCER_SHA256,'producer_review_sha256':PRODUCER_REVIEW_SHA256,'reconciler_source_sha256':RECONCILER_SHA256,'final_locked_kernel':final_kernel}
    create(dest/'acceptance.json',canonical(acceptance))
    print(json.dumps({'acceptance':acceptance,'sha256':hashlib.sha256(canonical(acceptance)).hexdigest()},sort_keys=True))
