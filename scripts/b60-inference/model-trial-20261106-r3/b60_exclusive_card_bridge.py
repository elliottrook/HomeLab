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

WORKLOAD = 'b60-qwen36-35b-failure-capture-v1'
KIND = 'b60-exclusive-card-capture'
ROOT = Path('/var/lib/local-ai-lab')
PACKAGE = Path('/usr/local/libexec/local-ai-lease/model-trial-20261106-r3')
BASE = Path('/usr/local/libexec/local-ai-lease/exclusive-session')
BASE_SHA = 'e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
MODEL_SHA = '671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7'
FILES = {'model_trial.py', 'namespace_mount.py', 'fixed_command.py',
         'guest_requests.py', 'guest_supervisor.py', 'backup_chain_history.py',
         'legacy_requests.py', 'request_failure_capture.py', 'news_xpu_boundary.py'}
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
            and row['end_epoch'] - row['start_epoch'] == 2700
            and row.get('restore_buffer_seconds') == 900
            and row['start_epoch'] <= now <= row['start_epoch'] + 120,
            'BRIDGE_BOOKING_WINDOW')
    expected = dict(workload_id=WORKLOAD, owner='b60-stream-a', runner_kind=KIND,
                    request_count=2, per_request_timeout_seconds=60,
                    deadline_seconds=1200, minimum_booking_seconds=2700,
                    recovery_reserve_seconds=900, retryable_session=False,
                    maximum_attempts=1, result_max_bytes=8192)
    require(all(getattr(spec, key, None) == value for key, value in expected.items()),
            'BRIDGE_REGISTRATION_DRIFT')


def validate_card(row, *, root=ROOT, package=PACKAGE, base=BASE, expected_uid=0):
    raw = protected(root/'model-trial-cards'/(row['booking_id']+'.json'), expected_uid=expected_uid)
    card = json.loads(raw)
    require(set(card) == {'schema', 'booking_id', 'start_epoch', 'end_epoch',
            'source_sha256', 'candidate_sha256', 'base_source_map_sha256', 'mode',
            'backup_history_sha256'}, 'BRIDGE_CARD_SCHEMA')
    require(card['schema'] == 'b60-fixed-model-trial.v1' and
            all(card[k] == row[k] for k in ('booking_id', 'start_epoch', 'end_epoch'))
            and card['candidate_sha256'] == MODEL_SHA and
            card['base_source_map_sha256'] == BASE_SHA and
            card['mode'] == 'qwen36-35b-reasoning-compatibility-v1', 'BRIDGE_CARD_IDENTITY')
    manifest = json.loads(protected(package/'manifest.json', expected_uid=expected_uid))
    require(set(manifest) == FILES and manifest == card['source_sha256'] and
            {p.name for p in package.glob('*.py')} == FILES, 'BRIDGE_SOURCE_CLOSURE')
    for name, sha in manifest.items():
        require(hashlib.sha256(protected(package/name, expected_uid=expected_uid, source=True)).hexdigest() == sha,
                'BRIDGE_SOURCE_DRIFT')
    pins = {p.name: hashlib.sha256(protected(p, expected_uid=expected_uid, source=True)).hexdigest()
            for p in base.glob('*.py')}
    require(len(pins) == 30 and hashlib.sha256(canonical(pins)).hexdigest() == BASE_SHA,
            'BRIDGE_BASE_SOURCE_DRIFT')
    return hashlib.sha256(raw).hexdigest()


def dispatch(row, spec, *, clock=time.time, runner=subprocess.run):
    require(os.geteuid() == 0 and os.uname().nodename == 'proxmox', 'BRIDGE_HOST_IDENTITY')
    validate_row(row, spec, int(clock()))
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
    result = runner(['/usr/bin/python3', '-B', str(PACKAGE/'model_trial.py'),
                     'launch', '--booking-id', row['booking_id']],
                    capture_output=True, text=True, timeout=25, check=False)
    require(result.returncode == 0, 'BRIDGE_OWNER_LAUNCH_FAILED')
    print(json.dumps({'state': 'owner-launched', 'booking_id': row['booking_id'],
                      'workload': WORKLOAD, 'qualification_claimed': False}, sort_keys=True))
    return 0
