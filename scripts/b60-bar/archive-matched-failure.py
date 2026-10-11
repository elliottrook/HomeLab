#!/usr/bin/env python3
"""Persist only the exact failed candidate invocation and recovery evidence."""
import hashlib
import json
import os
import re
import subprocess
import argparse
from pathlib import Path

def command(*args):
    return subprocess.check_output(args, text=True)

def guest(n, *args):
    return command('pct', 'exec', str(n), '--', *args)

def immutable(path, text):
    data = text.encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return hashlib.sha256(data).hexdigest()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fusion-disabled-retry', action='store_true')
retry = parser.parse_args().fusion_disabled_retry
prefix = 'fusion-off-sycl-failure-20261010' if retry else 'matched-sycl-failure-20261010'
invocation = guest(110, 'systemctl', 'show', 'aster-b60-candidate.service', '-p', 'InvocationID', '--value').strip()
assert re.fullmatch(r'[0-9a-f]{32}', invocation)
if not retry:
    assert invocation == '5e4a34e8ebac4a0fbe1a64baf284a687'
log = guest(110, 'journalctl', '_SYSTEMD_INVOCATION_ID=' + invocation, '--no-pager')
assert 'ggml_sycl_op_rms_norm' in log or 'Error OP RMS_NORM' in log
assert 'UR_RESULT_ERROR_UNSUPPORTED_FEATURE' in log
# Exact candidate ran no user requests. Keep only public diagnostics/backtrace,
# excluding the systemd command line and any request/content/header records.
safe = '\n'.join(line for line in log.splitlines()
                 if any(mark in line for mark in ['libggml', 'libsycl', 'libllama', 'libstdc++',
                                                   'libc.so', 'llama-server() [', 'what():',
                                                   'terminate called', 'threadpool init'])) + '\n'
safe += '\n'.join(line for line in log.splitlines()
                  if any(mark in line for mark in ['Error OP RMS_NORM', 'Exception caught at file:',
                                                    'Main process exited', 'Failed with result'])) + '\n'
root = Path('/var/lib/b60-inference/evidence')
root.mkdir(parents=True, exist_ok=True)
trace = root / (prefix + '.log')
trace_hash = immutable(trace, safe)
state = guest(110, 'systemctl', 'show', 'aster-llama.service', '-p', 'ActiveState', '-p', 'NRestarts')
assert 'ActiveState=active' in state and 'NRestarts=0' in state
health = json.loads(guest(110, 'curl', '-fsS', '--max-time', '10', 'http://192.168.70.12:11435/health'))
assert health['status'] == 'ok'
assert guest(114, 'systemctl', 'is-active', 'news-aggregator-ingest.timer', 'news-aggregator-digest.timer').split() == ['active', 'active']
operation = 'ggml_sycl_op_rms_norm_fused' if 'ggml_sycl_op_rms_norm_fused' in log else 'RMS_NORM (unfused)'
failure = {'invocation_id': invocation, 'result': 'exit-code 1 during startup compute warmup' if retry else 'ABRT during startup compute warmup',
           'error': 'UR_RESULT_ERROR_UNSUPPORTED_FEATURE', 'operation': operation,
           'sanitized_trace_sha256': trace_hash, 'accepted_service_state': state.strip(),
           'accepted_health': health, 'news_timers_active': True,
           'sycl_measured_repetitions': 0, 'automatic_retry_performed': False}
path = root / (prefix + '.json')
digest = immutable(path, json.dumps(failure, sort_keys=True) + '\n')
print(json.dumps({'evidence': failure, 'record_sha256': digest}, sort_keys=True))
