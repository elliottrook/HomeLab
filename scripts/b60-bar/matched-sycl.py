#!/usr/bin/env python3
"""One bounded same-model backend trial; run on Proxmox after guarded preflight."""
import json
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import re

sys.path.insert(0, '/run/b60-matched-sycl')
import guard

TZ = ZoneInfo('America/Vancouver')
ROOT = '/run/b60-matched-sycl'
OUT = '/var/lib/b60-inference/evidence/matched-sycl-20261010'
FAULT = r'GPU HANG|wedged|device lost|DMAR.*(fault|error)|IOMMU.*\sfault|Out of memory|oom-kill|BUG:|Oops:'
INSTRUMENTED = False
EXCLUSIVE = False
EXCLUSIVE_DEADLINE = None

def run(args, timeout=180, okay=(0,)):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if p.returncode not in okay:
        raise RuntimeError(f'command failed {args[:6]}: {p.returncode}')
    return p.stdout

def guest(n, *args, **kw):
    return run(['pct', 'exec', str(n), '--', *args], **kw)

def gates(unit):
    now = datetime.now(TZ)
    if EXCLUSIVE:
        if EXCLUSIVE_DEADLINE is None or now >= EXCLUSIVE_DEADLINE:
            raise RuntimeError('bounded exclusive experiment deadline')
    elif INSTRUMENTED:
        if now.date().isoformat() != '2026-10-10' or not ((now.hour == 22 and now.minute >= 15) or (now.hour == 23 and now.minute < 20)):
            raise RuntimeError('approved instrumented run 23:20 load cutoff')
    elif now.hour != 22 or now.minute < 15:
        raise RuntimeError('outside this bounded 22:15 trial')
    if not (INSTRUMENTED or EXCLUSIVE) and now.minute >= 55:
        raise RuntimeError('conservative 22:55 load cutoff')
    guest(110, 'systemctl', 'is-active', '--quiet', unit)
    health = json.loads(guest(110, 'curl', '-fsS', '--max-time', '10', 'http://192.168.70.12:11435/health'))
    assert health['status'] == 'ok'
    kernel = run(['journalctl', '-b', '-k', '--no-pager'])
    if not kernel.strip() or re.search(FAULT, kernel, re.IGNORECASE):
        raise RuntimeError('kernel failure or unavailable scan')
    guest(110, 'python3', '-c', 'import shutil; assert shutil.disk_usage("/").free>=20*1024**3; m=dict(line.split(":",1) for line in open("/proc/meminfo")); assert int(m["MemAvailable"].split()[0])*1024>=4*1024**3')

def suite(label, unit, repetitions=None):
    for rep in (repetitions if repetitions is not None else ['warmup', '1', '2', '3', '4', '5']):
        gates(unit)
        target = f'{OUT}-{label}-{rep}.json'
        print(f'BEGIN {label} {rep}', flush=True)
        result = guest(114, 'timeout', '180', 'python3', ROOT + '/runner.py',
                       '--endpoint', 'http://192.168.70.12:11435',
                       '--api-key-file', '/root/.news-aggregator-llama-key',
                       '--cases', ROOT + '/cases.json', '--label', f'{label}-{rep}',
                       '--output', target, '--max-tokens', '256', '--timeout', '60',
                       '--fail-fast-runtime', timeout=190, okay=(0, 1))
        print(result, flush=True)
        check = 'import json,sys; d=json.load(open(sys.argv[1])); assert len(d["results"])==16; assert all(r["elapsed_seconds"] is not None for r in d["results"]); assert d["pass_count"]>=12; assert {r["id"] for r in d["results"] if not r["passed"]}<={"stale-news","contradictory-sources","missing-evidence","private-public-join"}'
        guest(114, 'python3', '-c', check, target)
        gates(unit)

def restore():
    guard.execute_finalizer()
    print(guest(114, 'python3', '/run/b60-bar-validate-generation.py'), flush=True)
    restore_news()

def restore_news():
    # An owner-disabled schedule is a reservation, not a restoration failure.
    for unit in ['news-aggregator-ingest.timer', 'news-aggregator-digest.timer']:
        enabled = guest(114, 'systemctl', 'is-enabled', unit, okay=(0,1)).strip()
        if enabled in ['enabled', 'enabled-runtime']:
            guest(114, 'systemctl', 'start', unit)
        elif enabled != 'disabled':
            raise RuntimeError('unexpected news schedule enablement state')

def main(fusion_disabled_retry=False, instrumented=False, exclusive=False):
    global OUT, INSTRUMENTED, EXCLUSIVE, EXCLUSIVE_DEADLINE
    INSTRUMENTED = instrumented
    EXCLUSIVE = exclusive
    if exclusive:
        OUT = '/var/lib/b60-inference/evidence/matched-sycl-exclusive-20261010'
    elif instrumented:
        OUT = '/var/lib/b60-inference/evidence/matched-sycl-instrumented-20261010'
    elif fusion_disabled_retry:
        OUT = '/var/lib/b60-inference/evidence/matched-sycl-fusion-off-20261010'
    # The separate host watchdog remains armed until verified restoration.
    with open(ROOT + ('/preflight-exclusive.json' if exclusive else '/preflight-instrumented.json' if instrumented else '/preflight-fusion-retry.json' if fusion_disabled_retry else '/preflight.json')) as f:
        preflight = json.load(f)
    # Already validated in-window; require unchanged, recently recorded evidence.
    age = datetime.now(TZ) - guard.parse_time(preflight['collected_at'])
    assert 0 <= age.total_seconds() <= 600
    if exclusive:
        approved = guard.validate_preflight(preflight, datetime.now(TZ), 20, approved_exclusive_session=True)
        EXCLUSIVE_DEADLINE = guard.parse_time(approved['experiment_deadline'])
    elif instrumented:
        guard.validate_preflight(preflight, datetime.now(TZ), 16, approved_instrumented_run=True)
    elif fusion_disabled_retry:
        guard.validate_preflight(preflight, datetime.now(TZ), 25, approved_fusion_retry=True)
    for label in ['vulkan-pre', 'sycl', 'vulkan-post']:
        for rep in ['warmup', '1', '2', '3', '4', '5']:
            guest(114, 'test', '!', '-e', f'{OUT}-{label}-{rep}.json')
    guest(110, 'python3', '-c', 'import shutil; assert shutil.disk_usage("/").free >= 20*1024**3')
    candidate_started = False
    try:
        guest(114, 'systemctl', 'stop', 'news-aggregator-ingest.timer', 'news-aggregator-digest.timer')
        for service in ['news-aggregator-ingest.service', 'news-aggregator-digest.service']:
            assert guest(114, 'systemctl', 'is-active', service, okay=(3,)).strip() == 'inactive'
        suite('vulkan-pre', 'aster-llama.service')
        candidate_started = True
        guest(110, 'systemctl', 'stop', 'aster-llama.service')
        time.sleep(30)
        libs = guest(110, 'sh', '-c', 'find /dev/shm/b60-oneapi-trial-20261010/root -type f -name "*.so*" -printf "%h\\n" | sort -u | paste -sd:').strip()
        libs = '/opt/b60-level-zero-trial-20261010/root/usr/local/lib:/opt/b60-level-zero-trial-20261010/root/usr/lib/x86_64-linux-gnu:' + libs
        if instrumented or exclusive:
            libs = '/dev/shm/b60-loader-1331-trial-20261010/root/usr/lib/x86_64-linux-gnu:' + libs
        guest(110, 'systemd-run', '--unit=aster-b60-candidate', '--property=User=ollama',
              '--property=Group=ollama', '--property=SupplementaryGroups=video render',
              '--property=Restart=no', '--property=RuntimeMaxSec=900', '--property=TimeoutStopSec=30',
              '--property=LimitCORE=0',
              '--setenv=LD_LIBRARY_PATH=' + libs, '--setenv=ONEAPI_DEVICE_SELECTOR=level_zero:gpu',
              *(['--setenv=GGML_SYCL_ENABLE_FUSION=0'] if fusion_disabled_retry or instrumented or exclusive else []),
              '/opt/b60-level-zero-trial-20261010/llama-sycl-fp32/llama-b11429/llama-server',
              '-m', '/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf',
              '-ngl', '999', '-c', '8192', '-np', '1', '-t', '4', '-tb', '4',
              '-b', '256', '-ub', '128', '-fa', 'on', '-ctk', 'q4_0', '-ctv', 'q4_0',
              '--jinja', '--reasoning', 'off', '--reasoning-budget', '0',
              '--log-verbosity', '4',
              '--host', '192.168.70.12', '--port', '11435',
              '--api-key-file', '/etc/aster-llama-api-keys', '--metrics')
        for _ in range(60):
            state = guest(110, 'systemctl', 'is-active', 'aster-b60-candidate.service', okay=(0,3)).strip()
            if state in ['failed', 'inactive']:
                raise RuntimeError('candidate stopped during startup; no retry')
            health = guest(110, 'curl', '-fsS', '--max-time', '5', 'http://192.168.70.12:11435/health', okay=(0,7,22,28))
            if health and json.loads(health).get('status') == 'ok':
                gates('aster-b60-candidate.service')
                break
            time.sleep(5)
        else:
            raise RuntimeError('candidate not ready')
        invocation = guest(110, 'systemctl', 'show', 'aster-b60-candidate.service', '-p', 'InvocationID', '--value').strip()
        assert re.fullmatch(r'[0-9a-f]{32}', invocation)
        log = guest(110, 'journalctl', '_SYSTEMD_INVOCATION_ID=' + invocation, '--no-pager')
        # Print only non-secret startup/offload facts, never complete logs.
        for line in log.splitlines():
            if any(word in line for word in ['offloaded', 'SYCL', 'buffer size', 'error:', 'unsupported']):
                print(line, flush=True)
        assert 'offloaded' in log and 'SYCL' in log
        offload = re.search(r'offloaded (\d+)/(\d+) layers', log)
        assert offload and offload.group(1) == offload.group(2), 'CPU layer fallback'
        print(guest(114, 'python3', '/run/b60-bar-validate-generation.py'), flush=True)
        suite('sycl', 'aster-b60-candidate.service')
    finally:
        if candidate_started:
            restore()
        else:
            restore_news()
    suite('vulkan-post', 'aster-llama.service')
    run(['systemctl', 'stop', 'b60-exclusive-restore.timer' if exclusive else 'b60-instrumented-restore.timer' if instrumented else 'b60-fusion-restore.timer' if fusion_disabled_retry else 'b60-matched-restore.timer'])
    print('MATCHED TRIAL COMPLETE; ACCEPTED PRODUCTION RESTORED', flush=True)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fusion-disabled-retry', action='store_true')
    parser.add_argument('--instrumented', action='store_true')
    parser.add_argument('--exclusive', action='store_true', help='Owner-reserved B60 session; rolling 30-minute experiments, not calendar cutoff')
    args = parser.parse_args()
    main(args.fusion_disabled_retry, args.instrumented, args.exclusive)
