#!/bin/sh
# Run only after the exact two-file production deployment has been approved.
# This script never grants permissions and never auto-restores unsafe old code.
set -eu
umask 077
[ "${1:-}" = "--approved-stage1-window" ] || { echo 'Explicit Stage1 approval and maintenance window required' >&2; exit 2; }
[ "$(id -u)" = 0 ] || { echo 'Run inside LXC104 as root' >&2; exit 2; }
release=/var/tmp/aster-m1-stage1-20260925
live=/opt/homelab-broker
database=/var/lib/homelab-broker/broker.db
export PYTHONDONTWRITEBYTECODE=1

python3 "$release/stage1_preflight.py" --release "$release"
# A maintenance agreement is required as well as this immediate socket check.
python3 - <<'PY'
import re,subprocess
services=('homelab-broker.service','homelab-broker-approval.service')
pids=set()
for service in services:
    assert subprocess.check_output(['systemctl','is-active',service],text=True).strip()=='active'
    pid=subprocess.check_output(['systemctl','show',service,'--property=MainPID','--value'],text=True).strip()
    assert int(pid)>1
    pids.add(pid)
for line in subprocess.check_output(['ss','-xnpH','state','connected'],text=True).splitlines():
    for pid,fd in re.findall(r'pid=(\d+),fd=(\d+)',line):
        if pid in pids and int(fd)>2:
            raise SystemExit('ABORT: broker has an active connection; coordinate and recheck')
PY
checkpoint=/var/lib/homelab-broker/rollback/m1-stage1-$(date -u +%Y%m%dT%H%M%SZ)
export checkpoint
mkdir -p /var/lib/homelab-broker/rollback
chmod 0700 /var/lib/homelab-broker/rollback
mkdir -m 0700 "$checkpoint"
# A failure after entering maintenance leaves both entrypoints stopped.
# The trap never restarts potentially inconsistent or unsafe code.
trap 'result=$?; if [ "$result" -ne 0 ]; then systemctl stop homelab-broker-approval.service homelab-broker.service || true; fi; exit "$result"' 0
systemctl stop homelab-broker-approval.service homelab-broker.service
for service in homelab-broker.service homelab-broker-approval.service; do
    [ "$(systemctl show "$service" --property=MainPID --value)" = 0 ]
done
python3 "$release/stage1_preflight.py" --release "$release"
python3 - <<'PY'
import hashlib,json,os,shutil,sqlite3
from pathlib import Path
checkpoint=Path(os.environ['checkpoint'])
source=Path('/var/lib/homelab-broker/broker.db')
assert shutil.disk_usage(source.parent).free > max(64*1024*1024,source.stat().st_size*4)
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as live:
    with sqlite3.connect(checkpoint/'broker.db') as backup:
        live.backup(backup)
        assert backup.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    with sqlite3.connect(checkpoint/'broker.db') as backup:
        with sqlite3.connect(checkpoint/'restore-check.db') as restored:
            backup.backup(restored)
            assert restored.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            counts=restored.execute('SELECT status,COUNT(*) FROM requests GROUP BY status ORDER BY status').fetchall()
            assert counts==live.execute('SELECT status,COUNT(*) FROM requests GROUP BY status ORDER BY status').fetchall()
for name in ('broker_core.py','broker_service.py'):
    shutil.copy2(Path('/opt/homelab-broker')/name,checkpoint/name)
(checkpoint/'verification.json').write_text(json.dumps({'request_counts':counts,'database_sha256':hashlib.sha256((checkpoint/'broker.db').read_bytes()).hexdigest()}))
for name in ('broker.db','restore-check.db','verification.json'):
    (checkpoint/name).chmod(0o600)
print('Verified checkpoint: '+str(checkpoint))
PY
# Stop on failing staged tests before replacing source.
(cd "$release" && python3 -m unittest test_broker_core test_broker_service test_adaptive_foundation_regressions test_stage1_preflight)
(cd "$release" && python3 verify_legacy_approval.py --approval-service "$live/broker_approval_service.py")
for name in broker_core.py broker_service.py; do
    install -o root -g root -m 0644 "$release/$name" "$live/$name.m1-new"
    mv "$live/$name.m1-new" "$live/$name"
done
runuser -u hlabroker -- env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$live" python3 -c 'from broker_core import BrokerStore; s=BrokerStore("/var/lib/homelab-broker/broker.db"); s.close()'
python3 - <<'PY'
import hashlib,json,os,sqlite3
from pathlib import Path
release=Path('/var/tmp/aster-m1-stage1-20260925')
manifest=json.loads((release/'manifest.json').read_text())
for name in manifest['install_files']:
    assert hashlib.sha256((Path('/opt/homelab-broker')/name).read_bytes()).hexdigest()==manifest['files'][name]
with sqlite3.connect('file:/var/lib/homelab-broker/broker.db?mode=ro',uri=True) as database:
    assert database.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    counts=database.execute('SELECT status,COUNT(*) FROM requests GROUP BY status ORDER BY status').fetchall()
expected=json.loads((Path(os.environ['checkpoint'])/'verification.json').read_text())['request_counts']
assert [list(row) for row in counts]==expected
PY
systemctl start homelab-broker.service homelab-broker-approval.service
systemctl is-active homelab-broker.service homelab-broker-approval.service
python3 - <<'PYHEALTH'
import json,subprocess
response=json.loads(subprocess.check_output(['runuser','-u','hlabagent','--','/usr/local/bin/homelab-broker-client','{"method":"health"}'],text=True,timeout=5))
assert response.get('ok') is True and response.get('result',{}).get('status')=='ok'
print('Registered-peer health check passed')
PYHEALTH
printf '%s\n' 'Stage1 installed; complete the documented socket/HTTP checks and observation window.'
printf 'Recovery checkpoint: %s\n' "$checkpoint"
