"""Registered fixed-card dispatcher; the qualified inner owner is sole claimant.

No GPU/runtime import, arbitrary command, generic booking claim, model retry,
service operation or recovery implementation exists here. Use a fresh Python
subprocess so the global registry's modules cannot replace the accepted inner
controller's identically named modules in sys.modules.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

WORKLOAD = 'b60-entry-backend-preservation-qualification-v1'
KIND = 'b60-entry-rescue-card'
ROOT = Path('/var/lib/local-ai-lab')
PACKAGE = Path('/usr/local/libexec/local-ai-lease/entry-rescue-qualification-20261106-r7')
BASE = Path('/usr/local/libexec/local-ai-lease/exclusive-session')
BASE_SHA = 'e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
INCIDENT = 'b60-xe-20261106-1794002063'
INCIDENT_SHA = '7c1355adec390764cd970036233c1a70325d224b387e751dff4ef06db0e5cc6e'
FILES = {'qualification.py','entry_recovery.py','backup_chain_history.py','guest_entry_scope.py'}
ID = re.compile(r'b60-exclusive-\d{8}-day-r[1-9][0-9]{0,2}')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def require(value, code):
    if value is not True:
        raise RuntimeError(code)


def protected(path, *, expected_uid=0, maximum=262144, source=False):
    path = Path(path)
    for parent in path.parents:
        if parent == Path('/'):
            continue
        s = parent.lstat()
        require(stat.S_ISDIR(s.st_mode) and s.st_uid == expected_uid and
                not s.st_mode & 0o022, 'BRIDGE_PARENT_CUSTODY')
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid == expected_uid and s.st_nlink == 1
            and not s.st_mode & 0o022 and s.st_size <= maximum and
            (source or stat.S_IMODE(s.st_mode) == 0o600), 'BRIDGE_FILE_CUSTODY')
    raw = path.read_bytes()
    require(len(raw) <= maximum, 'BRIDGE_FILE_SIZE')
    return raw


def validate_row(row, spec, now):
    require(isinstance(row, dict) and isinstance(row.get('booking_id'), str)
            and ID.fullmatch(row['booking_id']) is not None, 'BRIDGE_BOOKING_ID')
    require(row.get('workload') == WORKLOAD and row.get('owner') == 'b60-stream-a'
            and row.get('kind') == 'exclusive-stack' and row.get('state') == 'reserved',
            'BRIDGE_BOOKING_IDENTITY')
    require(type(row.get('start_epoch')) is int and type(row.get('end_epoch')) is int
            and row['end_epoch'] - row['start_epoch'] == 1800
            and row.get('restore_buffer_seconds') == 900
            and row['start_epoch'] <= now <= row['start_epoch'] + 120,
            'BRIDGE_BOOKING_WINDOW')
    expected = dict(workload_id=WORKLOAD, owner='b60-stream-a', runner_kind=KIND,
                    request_count=1, per_request_timeout_seconds=600,
                    deadline_seconds=600, minimum_booking_seconds=1800,
                    recovery_reserve_seconds=900, retryable_session=False,
                    maximum_attempts=1, result_max_bytes=8192)
    require(all(getattr(spec, key, None) == value for key, value in expected.items()),
            'BRIDGE_REGISTRATION_DRIFT')


def validate_card(row, *, root=ROOT, package=PACKAGE, base=BASE, expected_uid=0):
    raw=protected(root/'entry-rescue-cards'/(row['booking_id']+'.json'),expected_uid=expected_uid)
    card=json.loads(raw)
    require(set(card)=={'schema','booking_id','start_epoch','end_epoch','source_sha256','incident_sha256','backup_history_sha256','authorization_sha256'},'CARD_SCHEMA')
    require(card['schema']=='b60-entry-rescue-card.v1' and all(card[k]==row[k] for k in ('booking_id','start_epoch','end_epoch')) and card['incident_sha256']==INCIDENT_SHA,'CARD_IDENTITY')
    auth=protected(root/'entry-rescue-authorization.json',expected_uid=expected_uid)
    require(hashlib.sha256(auth).hexdigest()==card['authorization_sha256'],'AUTHORITY_PROVENANCE')
    manifest=json.loads(protected(package/'manifest.json',expected_uid=expected_uid))
    require(set(manifest)==FILES and manifest==card['source_sha256'] and {p.name for p in package.glob('*.py')}==FILES,'SOURCE_CLOSURE')
    for n,sha in manifest.items():require(hashlib.sha256(protected(package/n,source=True,expected_uid=expected_uid)).hexdigest()==sha,'SOURCE_DRIFT')
    pins={p.name:hashlib.sha256(protected(p,source=True,expected_uid=expected_uid)).hexdigest() for p in base.glob('*.py')}
    require(len(pins)==30 and hashlib.sha256(canonical(pins)).hexdigest()==BASE_SHA,'BASE_DRIFT')
    return hashlib.sha256(raw).hexdigest()

QUALIFICATION_SOURCE = {'backup_chain_history.py': '0ebecf301c0b4fccdd4f128fdef9d09163eaf4e54cf871156ec80e5a8777d5e6', 'fixed_command.py': '16a74cf21a53a5c9ec7e5bec3fe9eeb1dc58e37da0f31fb25e038f7f4d9a388c', 'guest_entry_scope.py': '6fe93b41702b83a935305225273567a1ff60de8dd281622da68e0a0747a34479', 'known_answer_requests.py': 'd0d305405222fe8dd301fc4216f8cfd1a00d04b539d0d300be282d9d1e5604de', 'qualification.py': '42af10d66f319bfe7c824b588cd869a2fac7f3740562fcb5297fd6c9c70ae91c'}
ACCEPTANCE_SOURCE_SHA = 'fcbd5f89b5707f68a2d91fd8b75644029f395fd7e4a72d90513f509e2351008d'
INDEPENDENT_POSTCHECK_SHA = '47238d1b6369210edb0e1d28e69929f308c70e8967c452c4b788f441ebe88539'

def validate_incident_closure(closure, post):
    require(set(closure)=={'schema','state','incident_id','original_open_sha256','qualification_booking_id','postcheck_sha256','accepted_epoch','acceptance_source_sha256'},'INCIDENT_CLOSURE_SCHEMA')
    require(closure['schema']=='b60-device-incident-closure.v1' and closure['state']=='CLOSED_FOR_ACCEPTED_SYCL_CONTINUATION' and closure['incident_id']==INCIDENT and closure['original_open_sha256']==INCIDENT_SHA and closure['qualification_booking_id']=='b60-exclusive-20261106-day-r5','INCIDENT_CLOSURE_IDENTITY')
    require(post.get('schema')=='b60-post-xe-independent-postcheck.v1' and post.get('booking_id')==closure['qualification_booking_id'] and post.get('original_incident_sha256')==INCIDENT_SHA,'INCIDENT_POSTCHECK_IDENTITY')
    for k in ('production_restored','unit_states_match_entry','persistent_mount_identity_matches','candidate_scope_empty','news_mount_preserved'):require(post.get(k) is True,'INCIDENT_RESTORATION_UNPROVEN')
    for k in ('manual_assistance_required','deadline_missed','trial_failed'):require(post.get(k) is False,'INCIDENT_RESTORATION_UNPROVEN')
    require(post.get('temporary_deny_gates')==0 and post.get('booking_state')=='complete' and post.get('booking_result_code')=='RESTORED','INCIDENT_RELEASE_UNPROVEN')
    require(post.get('all_five_checkpoint_verifications')=={g:True for g in ('104','110','114','115','116')},'INCIDENT_GUEST_RESTORATION_UNPROVEN')
    packet=post.get('answers',{});rows=packet.get('records',[])
    require(packet.get('schema')=='b60-post-xe-known-answer-packet.v1' and packet.get('state')=='passed' and packet.get('attempted_requests')==3 and packet.get('retries')==0 and len(rows)==3,'INCIDENT_CORRECTNESS_UNPROVEN')
    for i,row in enumerate(rows):require(row.get('request')==i+1 and row.get('predicate_passed') is True and row.get('outcome')=='passed' and row.get('http_status')==200 and row.get('finish_reason')=='stop','INCIDENT_CORRECTNESS_UNPROVEN')
    terminal=post.get('qualification_terminal',{})
    require(terminal.get('qualified') is True and terminal.get('session_outcome')=='complete-restored' and terminal.get('incident_sha256')==INCIDENT_SHA and terminal.get('answers_sha256')==hashlib.sha256(canonical(packet)).hexdigest(),'INCIDENT_TERMINAL_UNPROVEN')
    require(terminal.get('source_sha256')==post.get('source_sha256')==QUALIFICATION_SOURCE,'INCIDENT_QUALIFICATION_SOURCE')
    require(post.get('kernel',{}).get('new_hazards')==0 and post['kernel'].get('since_epoch')==1794002064 and post['kernel'].get('observed_epoch',0)>=post.get('finished_epoch',0),'INCIDENT_POST_RESTORATION_KERNEL')
    return True


def require_incident_closed():
    # Original evidence is never erased, modified or aged out. The separate
    # closure route requires actual fixed known answers AND exact restoration.
    parent=ROOT/'device-incidents'/INCIDENT
    raw=protected(parent/'open.json')
    require(hashlib.sha256(raw).hexdigest()==INCIDENT_SHA,'DEVICE_INCIDENT_EVIDENCE_DRIFT')
    original=json.loads(raw);require(original.get('incident_id')==INCIDENT and original.get('state')=='OPEN','DEVICE_INCIDENT_EVIDENCE_INVALID')
    require((parent/'closure.json').exists(),'DEVICE_INCIDENT_OPEN')
    closure=json.loads(protected(parent/'closure.json'))
    postraw=protected(parent/'postcheck.json',maximum=65536)
    require(hashlib.sha256(postraw).hexdigest()==closure.get('postcheck_sha256'),'INCIDENT_POSTCHECK_DRIFT')
    require(closure.get('acceptance_source_sha256')==ACCEPTANCE_SOURCE_SHA and hashlib.sha256(protected(parent/'acceptance-source.py',source=True)).hexdigest()==ACCEPTANCE_SOURCE_SHA,'INCIDENT_ACCEPTANCE_SOURCE_DRIFT')
    post=json.loads(postraw);validate_incident_closure(closure,post)
    review_raw=protected(parent/'independent-postcheck-acceptance.json',maximum=65536)
    require(hashlib.sha256(review_raw).hexdigest()==INDEPENDENT_POSTCHECK_SHA and post.get('historical_independent_postcheck_sha256')==INDEPENDENT_POSTCHECK_SHA,'INDEPENDENT_FULL_POSTCHECK_DRIFT')
    historical=json.loads(review_raw)['result']
    require(all(post.get('postcheck_kernel' if k=='kernel' else k)==v for k,v in historical.items()),'HISTORICAL_POSTCHECK_RELABELLED')
    profile_raw=protected(ROOT/'exclusive-activations/b60-exclusive-20261106-day-r5.json')
    require(hashlib.sha256(profile_raw).hexdigest()==post.get('current_profile_sha256') and json.loads(profile_raw)['guest_plans']==post.get('current_guest_plan_sha256'),'INCIDENT_PLAN_PROFILE_BINDING')

    required={'exclusive-sessions/b60-exclusive-20261106-day-r5/'+n for n in ('session.json','entry.json','qualification-answers.json','post-xe-terminal.json','qualification-residency.json','qualification-offload.json','qualification-effective-limits.json','qualification-kernel-after.json')}
    required|={'exclusive-releases/b60-exclusive-20261106-day-r5.json','reservations/records/b60-exclusive-20261106-day-r5.json','post-xe-cards/b60-exclusive-20261106-day-r5.json','arming-receipts/b60-exclusive-20261106-day-r5-post-xe.json'}
    hashes=post.get('record_sha256',{});require(required<=set(hashes),'INCIDENT_PROOF_CLOSURE')
    for name,sha in hashes.items():
        require(isinstance(name,str) and not name.startswith('/') and '..' not in Path(name).parts,'INCIDENT_RECORD_PATH')
        require(hashlib.sha256(protected(ROOT/name,maximum=262144)).hexdigest()==sha,'INCIDENT_PROOF_DRIFT')
    package=BASE.parent/'post-xe-qualification-20261106-r5'
    for name,sha in post['source_sha256'].items():require(hashlib.sha256(protected(package/name,source=True)).hexdigest()==sha,'INCIDENT_SOURCE_DRIFT')
    return {'closure_sha256':hashlib.sha256(protected(parent/'closure.json')).hexdigest(),'qualified_booking_id':closure['qualification_booking_id'],'postcheck_sha256':closure['postcheck_sha256']}

def dispatch(row, spec, *, clock=time.time, runner=subprocess.run):
    require(os.geteuid() == 0 and os.uname().nodename == 'proxmox', 'BRIDGE_HOST_IDENTITY')
    validate_row(row, spec, int(clock()))
    require_incident_closed()
    card_sha = validate_card(row)
    # Atomic once-only intent: the normal minute dispatcher never sees reserved
    # records, and a repeated dedicated-clock invocation cannot relaunch them.
    root = ROOT/'exclusive-dispatch'
    root.mkdir(mode=0o700, exist_ok=True)
    s = root.lstat()
    require(stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and stat.S_IMODE(s.st_mode) == 0o700,
            'BRIDGE_DISPATCH_CUSTODY')
    intent = canonical({'schema': 'b60-registered-exclusive-dispatch.v1',
        'booking_id': row['booking_id'], 'workload': WORKLOAD,
        'card_sha256': card_sha, 'booking_identity': {k:row[k] for k in ('booking_id','owner','kind','workload','start_epoch','end_epoch')}, 'booking_sha256': hashlib.sha256(canonical(row)).hexdigest(),
        'dispatched_epoch': int(clock()), 'claimant': 'qualified-inner-owner-only'})
    fd = os.open(root/(row['booking_id']+'.json'), os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(intent); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(root, os.O_RDONLY); os.fsync(fd); os.close(fd)
    # No parent host-directory flock is held while the new owner starts its
    # independent admission. Raw child stdout/stderr never crosses this bridge.
    result = runner(['/usr/bin/python3', '-B', str(PACKAGE/'qualification.py'),
                     'launch', '--booking-id', row['booking_id']],
                    capture_output=True, text=True, timeout=25, check=False)
    require(result.returncode == 0, 'BRIDGE_OWNER_LAUNCH_FAILED')
    print(json.dumps({'state': 'owner-launched', 'booking_id': row['booking_id'],
                      'workload': WORKLOAD, 'qualification_claimed': False}, sort_keys=True))
    return 0
