#!/usr/bin/env python3
"""Host-side fresh gates; bounded TrueNAS result supplied from separate SSH check."""
import json
import os
import re
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import argparse
sys.path.insert(0, '/run/b60-matched-sycl')
import guard
TZ = ZoneInfo('America/Vancouver')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--verified-mirror-size', type=int, required=True)
parser.add_argument('--verified-mirror-state', choices=['SUCCESS'], required=True)
parser.add_argument('--verified-mirror-finished-at', required=True)
parser.add_argument('--mirror-checked-at', required=True)
parser.add_argument('--instrumented', action='store_true')
parser.add_argument('--exclusive', action='store_true')
parser.add_argument('--run-id')
parser.add_argument('--precision',choices=['fp32','fp16'],default='fp32')
parser.add_argument('--backup-path',default='/mnt/backups/dump/vzdump-lxc-110-2026_10_10-02_39_32.tar.zst')
parser.add_argument('--backup-size',type=int,default=38852679165)
parser.add_argument('--accepted-sycl-unit-sha256',help='Explicit accepted persistent SYCL profile, only after promotion validation')
options = parser.parse_args()
assert options.run_id is None or (options.exclusive and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',options.run_id))
assert options.exclusive or datetime.now(TZ).date().isoformat() == '2026-10-10', 'one-time authorization expired'
assert options.verified_mirror_size == options.backup_size and options.backup_size>1024**3
assert re.fullmatch(r'/mnt/backups/dump/vzdump-lxc-110-\d{4}_\d{2}_\d{2}-\d{2}_\d{2}_\d{2}\.tar\.zst',options.backup_path)
mirror_age = (datetime.now(TZ) - guard.parse_time(options.mirror_checked_at)).total_seconds()
assert 0 <= mirror_age <= 300, 'external bounded mirror verification must be fresh'
def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=120).stdout
def guest(n, *args):
    return run('pct', 'exec', str(n), '--', *args)
backup = options.backup_path
stat = os.stat(backup)
assert stat.st_size == options.backup_size
candidate='/opt/b60-level-zero-trial-20261010/llama-sycl-'+options.precision+'/llama-b11429/'
accepted=guard.ACCEPTED_BINARY_PATH
if options.accepted_sycl_unit_sha256:
    assert options.exclusive and options.precision=='fp16' and re.fullmatch(r'[0-9a-f]{64}',options.accepted_sycl_unit_sha256)
    manifest=json.loads(guest(110,'python3','-c','import json; print(json.dumps(json.load(open("/opt/aster-sycl-b11429/manifest.json"))))'))
    assert manifest['unit_sha256']==options.accepted_sycl_unit_sha256 and manifest['volatile_dependencies'] is False
    assert manifest['server_sha256']=='0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
    candidate='/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/'
    accepted=candidate+'llama-server'
    # Validation profile only in this collector process. Legacy Vulkan finalizer
    # remains untouched; native trials restore through the explicit SYCL path.
    guard.ACCEPTED_BINARY_SHA256=manifest['server_sha256']
    guard.ACCEPTED_UNIT_SHA256=options.accepted_sycl_unit_sha256
hashes = guest(110, 'sha256sum', accepted, '/etc/systemd/system/aster-llama.service', '/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf', candidate+'llama-server',candidate+'libggml-sycl.so.0.26.0').splitlines()
assert hashes[2].split()[0] == 'cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13'
assert hashes[3].split()[0] == '0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
assert hashes[4].split()[0] == ('58757946256db139bab7ddab56dbe6e8d5503bb41518eb25bfc734c175c68591' if options.precision=='fp16' else 'd267ea962c1166e964cc7bb771a9b7dd7c9b1405d5c5156463995a9f4e1da2d7')
assert guest(110, 'systemctl', 'is-active', 'aster-llama.service').strip() == 'active'
assert json.loads(guest(114, 'curl', '-fsS', '--max-time', '10', 'http://192.168.70.10:9120/health'))['status'] == 'ok'
kernel = run('journalctl', '-b', '-k', '--no-pager')
assert kernel.strip(), 'kernel log unavailable'
assert not re.search(r'GPU HANG|wedged|device lost|DMAR.*(fault|error)|IOMMU.*\sfault|Out of memory|oom-kill|BUG:|Oops:', kernel, re.I)
telemetry = dict(line.split('=',1) for line in guest(110,'sh','/run/b60-bar-telemetry.sh').splitlines())
assert int(telemetry['gpu_temp_pkg_millic']) < 80000 and int(telemetry['gpu_temp_vram_millic']) < 80000
vulkan = guest(110, 'vulkaninfo', '--summary')
assert 'BMG G21' in vulkan
free = int(guest(110, 'python3', '-c', 'import shutil; print(shutil.disk_usage("/").free)').strip())
health = json.loads(guest(110, 'curl', '-fsS', '--max-time', '10', 'http://192.168.70.12:11435/health'))['status']
data = dict(collected_at=datetime.now(TZ).isoformat(), backup_completed_at=datetime.fromtimestamp(stat.st_mtime,TZ).isoformat(),
            mirror_completed_at=options.verified_mirror_finished_at, mirror_state=options.verified_mirror_state, service_health=health,
            driver=run('readlink', '/sys/bus/pci/devices/0000:04:00.0/driver').strip().split('/')[-1],
            vulkan_device='Intel(R) Arc(tm) Pro B60 Graphics (BMG G21)', binary_sha256=hashes[0].split()[0],
            unit_sha256=hashes[1].split()[0], disk_free_bytes=free,
            ram_available_bytes=int(telemetry['ram_available_kib'])*1024,
            vram_headroom_bytes=25669140480-int(telemetry['vram_resident_kib'])*1024)
guard.validate_preflight(data,datetime.now(TZ),20 if options.exclusive else 16 if options.instrumented else 9,
                        approved_loader_retry=not (options.instrumented or options.exclusive),
                        approved_instrumented_run=options.instrumented,
                        approved_exclusive_session=options.exclusive)
with open('/run/b60-matched-sycl/' + ('preflight-exclusive' + ('-'+options.run_id if options.run_id else '') + '.json' if options.exclusive else 'preflight-instrumented.json' if options.instrumented else 'preflight-loader-retry.json'),'x') as f:
    json.dump(data,f,indent=2)
print(json.dumps(data,indent=2))
