#!/usr/bin/env python3
"""Bounded TrueNAS reconciliation against the existing read-only Proxmox export.
Native rsync keeps delete=false. This step removes only pruned guest archives.
"""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/mnt/Recovery/guests/homelab-proxmox-guests')
STATE = Path('/mnt/Media/backup-ops/guest-retention-state.json')
ALLOWED = set(range(100, 118)) - {110}
PATTERN = re.compile(r'vzdump-(?:lxc|qemu)-(\d+)-(\d{4}_\d\d_\d\d-\d\d_\d\d_\d\d)\.(?:tar|vma)\.zst')

def command(args):
    return subprocess.check_output(args, text=True, timeout=180)

def inventory():
    output = command(['rsync', '--list-only', '--no-human-readable', '-e',
        'ssh -o BatchMode=yes -o ConnectTimeout=10 -i /root/.ssh/homelab_proxmox_pull_ed25519',
        'homelab-backup@192.168.50.10:./'])
    result = {}
    for line in output.splitlines():
        parts = line.split(None, 4)
        if len(parts) != 5 or not PATTERN.fullmatch(parts[4]):
            continue
        if not parts[0].startswith('-'):
            raise RuntimeError('Non-regular source archive')
        result[parts[4]] = int(parts[1])
    return result

def guest(name):
    return int(PATTERN.fullmatch(name)[1])

def validate(source, local, previous=None, bootstrap=None):
    if not source:
        raise RuntimeError('Source empty')
    selected = {n: b for n, b in source.items() if guest(n) in ALLOWED}
    if {guest(n) for n in selected} != ALLOWED:
        raise RuntimeError('Expected guest missing')
    for vm in ALLOWED:
        names = sorted(n for n in selected if guest(n) == vm)
        if len(names) < 7:
            raise RuntimeError('Fewer than seven recovery points for guest ' + str(vm))
        stamp = dt.datetime.strptime(PATTERN.fullmatch(names[-1])[2], '%Y_%m_%d-%H_%M_%S')
        age = (dt.datetime.now() - stamp).total_seconds()
        if not -3600 < age < 48 * 3600:
            raise RuntimeError('Latest backup is stale')
    for n, b in selected.items():
        if b < 1000000 or local.get(n) != b:
            raise RuntimeError('Retained archive missing, small or size mismatch: ' + n)
    candidates = {n: b for n, b in local.items() if guest(n) in ALLOWED and n not in source}
    if bootstrap is not None:
        approved = {x['name']: x['bytes'] for x in bootstrap['local_candidates']}
        if candidates != approved:
            raise RuntimeError('Bootstrap candidates differ from approved manifest')
        if selected != {x['name']: x['bytes'] for x in bootstrap['retained']}:
            raise RuntimeError('Bootstrap retained set changed')
    else:
        if not previous:
            raise RuntimeError('Missing baseline')
        old = previous['source']
        if {guest(n) for n in source} != {guest(n) for n in old}:
            raise RuntimeError('Source guest set changed')
        if len(source) < len(old) * .8:
            raise RuntimeError('Source inventory shrink exceeded 20 percent')
        if len(candidates) > 25 or len(candidates) > max(1, len(local) * .2):
            raise RuntimeError('Deletion spike')
        for n, b in candidates.items():
            if old.get(n) != b:
                raise RuntimeError('Candidate was not present in previous good source inventory')
    return candidates

def save(data):
    STATE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    os.chmod(tmp, 0o600)
    os.replace(tmp, STATE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--bootstrap-manifest')
    args = parser.parse_args()
    os.environ['LC_ALL'] = 'C'
    with open('/run/guest-retention-reconcile.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        jobs = json.loads(command(['midclt', 'call', 'core.get_jobs']))
        if any(x['method'] == 'rsynctask.run' and x['state'] in ('RUNNING', 'WAITING') for x in jobs):
            raise RuntimeError('Rsync job active')
        task = json.loads(command(['midclt', 'call', 'rsynctask.query', '[["id","=",1]]']))[0]
        job = task.get('job') or {}
        ended = (job.get('time_finished') or {}).get('$date', 0) / 1000
        if job.get('state') != 'SUCCESS' or time.time() - ended > 30 * 3600:
            raise RuntimeError('Recent successful pull required')
        if not ROOT.is_dir() or ROOT.is_symlink():
            raise RuntimeError('Destination unavailable')
        stats = {p.name: p.lstat() for p in ROOT.iterdir() if PATTERN.fullmatch(p.name)}
        import stat
        if any(not stat.S_ISREG(s.st_mode) for s in stats.values()):
            raise RuntimeError('Non-regular local archive')
        local = {n: s.st_size for n, s in stats.items()}
        source = inventory()
        previous = json.loads(STATE.read_text()) if STATE.exists() else None
        bootstrap = json.loads(Path(args.bootstrap_manifest).read_text()) if args.bootstrap_manifest else None
        candidates = validate(source, local, previous, bootstrap)
        print(json.dumps({'candidates': len(candidates), 'bytes': sum(candidates.values()), 'execute': args.execute}), flush=True)
        if not args.execute:
            return
        if inventory() != source:
            raise RuntimeError('Source changed during planning')
        # The scheduled pull runs at 04:00; this bounded job runs at 06:00.
        # Abort if an operator started a pull during inventory collection.
        jobs = json.loads(command(['midclt', 'call', 'core.get_jobs']))
        if any(x['method'] == 'rsynctask.run' and x['state'] in ('RUNNING', 'WAITING') for x in jobs):
            raise RuntimeError('Rsync job started')
        for n in local:
            now = (ROOT / n).lstat()
            old = stats[n]
            if (now.st_ino, now.st_size, now.st_mtime_ns) != (old.st_ino, old.st_size, old.st_mtime_ns):
                raise RuntimeError('Destination changed')
        for n in sorted(candidates):
            (ROOT / n).unlink()
            print(json.dumps({'deleted': n, 'bytes': candidates[n]}), flush=True)
        save({'checked_epoch': time.time(), 'source': source, 'deleted_count': len(candidates),
              'deleted_bytes': sum(candidates.values()), 'status': 'success'})

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), flush=True)
        try:
            state = json.loads(STATE.read_text()) if STATE.exists() else {}
            state.update(status='failed', failed_epoch=time.time(), error=str(exc))
            save(state)
        except Exception:
            pass
        raise SystemExit(1)
