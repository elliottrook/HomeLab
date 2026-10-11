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
options = parser.parse_args()
assert datetime.now(TZ).date().isoformat() == '2026-10-10', 'one-time authorization expired'
assert options.verified_mirror_size == 38852679165
mirror_age = (datetime.now(TZ) - guard.parse_time(options.mirror_checked_at)).total_seconds()
assert 0 <= mirror_age <= 300, 'external bounded mirror verification must be fresh'
def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=120).stdout
def guest(n, *args):
    return run('pct', 'exec', str(n), '--', *args)
backup = '/mnt/backups/dump/vzdump-lxc-110-2026_10_10-02_39_32.tar.zst'
stat = os.stat(backup)
assert stat.st_size == 38852679165
hashes = guest(110, 'sha256sum', '/opt/llama.cpp-b11429/llama-server', '/etc/systemd/system/aster-llama.service', '/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf', '/opt/b60-level-zero-trial-20261010/llama-sycl-fp32/llama-b11429/llama-server').splitlines()
assert hashes[2].split()[0] == 'cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13'
assert hashes[3].split()[0] == '0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
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
guard.validate_preflight(data,datetime.now(TZ),9,approved_loader_retry=True)
with open('/run/b60-matched-sycl/preflight-loader-retry.json','x') as f:
    json.dump(data,f,indent=2)
print(json.dumps(data,indent=2))
