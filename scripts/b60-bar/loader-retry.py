#!/usr/bin/env python3
"""Explicitly approved Oct 10 loader-only retry; one model start, no retry loop."""
import json
import sys
import time
from datetime import datetime
sys.path.insert(0, '/run/b60-matched-sycl')
import matched_sycl as trial

ROOT = trial.ROOT
trial.OUT = '/var/lib/b60-inference/evidence/matched-sycl-loader-1331-20261010'

def main():
    with open(ROOT + '/preflight-loader-retry.json') as f:
        preflight = json.load(f)
    print(trial.guard.validate_preflight(preflight, datetime.now(trial.TZ), 9,
                                        approved_loader_retry=True), flush=True)
    assert datetime.now(trial.TZ).hour == 22 and datetime.now(trial.TZ).minute < 50
    # Reuse the five immutable immediately preceding Vulkan controls for variance.
    # One fresh full suite confirms production still has its known 12/16 behavior.
    def one_suite(label, unit):
        trial.suite(label, unit, repetitions=['warmup'])
    started = False
    try:
        trial.guest(114, 'systemctl', 'stop', 'news-aggregator-ingest.timer', 'news-aggregator-digest.timer')
        for unit in ['news-aggregator-ingest.service', 'news-aggregator-digest.service']:
            assert trial.guest(114, 'systemctl', 'is-active', unit, okay=(3,)).strip() == 'inactive'
        one_suite('vulkan-confirmation', 'aster-llama.service')
        trial.gates('aster-llama.service')
        started = True
        trial.guest(110, 'systemctl', 'stop', 'aster-llama.service')
        time.sleep(30)
        libs = trial.guest(110, 'sh', '-c', 'find /dev/shm/b60-oneapi-trial-20261010/root -type f -name "*.so*" -printf "%h\\n" | sort -u | paste -sd:').strip()
        libs = '/dev/shm/b60-loader-1331-trial-20261010/root/usr/lib/x86_64-linux-gnu:/opt/b60-level-zero-trial-20261010/root/usr/local/lib:/opt/b60-level-zero-trial-20261010/root/usr/lib/x86_64-linux-gnu:' + libs
        trial.guest(110, 'systemd-run', '--unit=aster-b60-candidate',
                    '--property=User=ollama', '--property=Group=ollama',
                    '--property=SupplementaryGroups=video render', '--property=Restart=no',
                    '--property=RuntimeMaxSec=480', '--property=TimeoutStopSec=30', '--property=LimitCORE=0',
                    '--setenv=LD_LIBRARY_PATH=' + libs, '--setenv=ONEAPI_DEVICE_SELECTOR=level_zero:gpu',
                    '--setenv=GGML_SYCL_ENABLE_FUSION=0',
                    '/opt/b60-level-zero-trial-20261010/llama-sycl-fp32/llama-b11429/llama-server',
                    '-m', '/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf',
                    '-ngl', '999', '-c', '8192', '-np', '1', '-t', '4', '-tb', '4',
                    '-b', '256', '-ub', '128', '-fa', 'on', '-ctk', 'q4_0', '-ctv', 'q4_0',
                    '--jinja', '--reasoning', 'off', '--reasoning-budget', '0',
                    '--log-verbosity', '4',
                    '--host', '192.168.70.12', '--port', '11435',
                    '--api-key-file', '/etc/aster-llama-api-keys', '--metrics')
        for _ in range(48):
            now = datetime.now(trial.TZ)
            if now.hour != 22 or now.minute >= 55:
                raise RuntimeError('22:55 load cutoff')
            state = trial.guest(110, 'systemctl', 'is-active', 'aster-b60-candidate.service', okay=(0,3)).strip()
            if state in ['failed', 'inactive']:
                raise RuntimeError('loader-corrected candidate failed startup; no retry')
            health = trial.guest(110, 'curl', '-fsS', '--max-time', '5', 'http://192.168.70.12:11435/health', okay=(0,7,22,28))
            if health and json.loads(health).get('status') == 'ok':
                break
            time.sleep(5)
        else:
            raise RuntimeError('startup readiness deadline')
        trial.gates('aster-b60-candidate.service')
        invocation = trial.guest(110, 'systemctl', 'show', 'aster-b60-candidate.service', '-p', 'InvocationID', '--value').strip()
        log = trial.guest(110, 'journalctl', '_SYSTEMD_INVOCATION_ID=' + invocation, '--no-pager')
        offload = trial.re.search(r'offloaded (\d+)/(\d+) layers', log)
        assert 'SYCL' in log and offload and offload.group(1) == offload.group(2)
        print(trial.guest(114, 'python3', '/run/b60-bar-validate-generation.py'), flush=True)
        one_suite('sycl-correctness', 'aster-b60-candidate.service')
        print('LOADER RETRY CORRECTNESS PASSED; NOT A COMPLETE MATCHED SPEED STUDY', flush=True)
    finally:
        if started:
            trial.restore()
        else:
            trial.restore_news()

if __name__ == '__main__':
    main()
