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
PACKAGE = Path('/usr/local/libexec/local-ai-lease/entry-rescue-qualification-20261106-r6')
BASE = Path('/usr/local/libexec/local-ai-lease/exclusive-session')
BASE_SHA = 'e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
MODEL_SHA = '671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7'
INCIDENT = 'b60-xe-20261106-1794002063'
INCIDENT_SHA = '7c1355adec390764cd970036233c1a70325d224b387e751dff4ef06db0e5cc6e'
FILES = {'qualification.py','entry_recovery.py','fixed_command.py','backup_chain_history.py','guest_entry_scope.py'}
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

def require_incident_closed():
    import importlib.util
    path=BASE.parent/'full-inference-pilot/b60_exclusive_card_bridge.py'
    raw=protected(path,source=True)
    require(hashlib.sha256(raw).hexdigest()=='079e16a415276562227f1645fe1e3ab64f5b0b41c1f453ae215935b1ca14f7d9','INCIDENT_GATE_SOURCE_DRIFT')
    sp=importlib.util.spec_from_file_location('fixed_accepted_incident_gate',path)
    gate=importlib.util.module_from_spec(sp);sp.loader.exec_module(gate)
    return gate.require_incident_closed()


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
