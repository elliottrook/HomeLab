#!/usr/bin/python3
"""Root-owned Proxmox forced-command adapter; stdin is a strict target/job pair."""
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

TARGETS = {"guest-104": 104, "guest-109": 109, "guest-111": 111, "guest-113": 113, "guest-116": 116}
STATE = Path("/var/lib/aster-lab-guest")
BACKUPS = Path("/mnt/backups/dump")


def outcome(state, code, **values):
    return {"state": state, "code": code, "coverage": "none", **values}


def save(path, value):
    candidate = path.with_suffix(".tmp")
    with candidate.open("w") as f:
        json.dump(value, f)
        f.flush()
        os.fsync(f.fileno())
    candidate.replace(path)


def validate(value):
    if not isinstance(value, dict) or set(value) != {"target", "id"}:
        raise ValueError()
    if not isinstance(value["target"], str) or value["target"] not in TARGETS or not isinstance(value["id"], str) or not re.fullmatch(r"[a-f0-9]{32}", value["id"]):
        raise ValueError()
    return value


def execute(value):
    target, jid = value["target"], value["id"]
    record = STATE / (jid + ".json")
    if record.exists():
        return json.loads(record.read_text()).get("result", outcome("unknown", "interrupted"))
    records = []
    for path in STATE.glob("*.json"):
        prior_record = json.loads(path.read_text())
        if prior_record.get("result", {}).get("state") in {"succeeded", "failed"} and prior_record["started"] < time.time()-30*86400:
            path.unlink()  # bounded adapter metadata, never an archive
        else:
            records.append(prior_record)
    if any("result" not in r or r["result"]["state"] == "unknown" for r in records):
        return outcome("unknown", "interrupted")
    retry_of = None
    if any(r["target"] == target and r["started"] > time.time()-3600 for r in records):
        ticket_path = STATE / (".retry-" + target)
        if not ticket_path.exists():
            return outcome("failed", "busy")
        ticket = json.loads(ticket_path.read_text())
        if not re.fullmatch(r"[a-f0-9]{32}", ticket.get("job", "")) or not time.time() <= ticket.get("expires", 0) <= time.time()+600:
            return outcome("failed", "busy")
        previous = json.loads((STATE / (ticket["job"]+".json")).read_text())
        if previous["target"] != target or previous.get("result", {}).get("state") != "failed":
            return outcome("failed", "busy")
        retry_of = ticket["job"]
        ticket_path.unlink()  # consume the root-issued, one-use retry ticket
    vmid = TARGETS[target]
    if not os.path.ismount("/mnt/backups") or not BACKUPS.is_dir():
        return outcome("failed", "adapter_failed")
    # Respect the existing scheduled backup window, plus native global lock.
    if 2 <= time.localtime().tm_hour < 6:
        return outcome("failed", "busy")
    status = subprocess.run(["/usr/sbin/pct", "status", str(vmid)], capture_output=True, text=True, timeout=15)
    if status.returncode or status.stdout.strip() != "status: running":
        return outcome("failed", "busy")
    config = Path(f"/etc/pve/lxc/{vmid}.conf").read_text()
    if re.search(r"^(lock|mp[0-9]+|hookscript):", config, re.M):
        return outcome("failed", "busy")
    defaults = Path("/etc/vzdump.conf").read_text()
    if re.search(r"^\s*script\s*:", defaults, re.M):
        return outcome("failed", "disabled")
    size = re.search(r"^rootfs:.*\bsize=(\d+(?:\.\d+)?)([GMT])(?:,|$)", config, re.M)
    prior = list(BACKUPS.glob(f"vzdump-lxc-{vmid}-*.tar.zst"))
    if not size or not prior:
        return outcome("failed", "verification_failed")
    root_bytes = float(size[1]) * {"M": 1024**2, "G": 1024**3, "T": 1024**4}[size[2]]
    estimate = max(root_bytes * 1.2, max(p.stat().st_size for p in prior) * 2)
    if estimate > 128 * 1024**3:
        return outcome("failed", "low_space")
    stat = os.statvfs(BACKUPS)
    if stat.f_bavail * stat.f_frsize < estimate + 512 * 1024**3:
        return outcome("failed", "low_space")
    started = time.time()
    checkpoint = {"target": target, "started": started, "retry_of": retry_of}
    save(record, checkpoint)
    with (STATE / "last-operation.log").open("wb") as log:
        try:
            command = ["/usr/bin/vzdump", str(vmid), "--storage", "backups", "--mode", "snapshot",
                       "--compress", "zstd", "--remove", "0", "--prune-backups", "keep-all=1",
                       "--lockwait", "0", "--bwlimit", "51200", "--zstd", "1"]
            code = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log, timeout=4800, umask=0o022).returncode
            if code:
                completed = outcome("failed", "adapter_failed")
            else:
                archives = [p for p in BACKUPS.glob(f"vzdump-lxc-{vmid}-*.tar.zst") if p not in prior and not p.is_symlink() and p.stat().st_mtime >= started-2]
                if len(archives) != 1:
                    raise ValueError()
                archive = archives[0]
                if not archive.stat().st_size:
                    raise ValueError()
                subprocess.run(["/usr/bin/zstd", "-t", str(archive)], check=True, stdout=log, stderr=log, timeout=600)
                subprocess.run(["/usr/bin/tar", "--zstd", "-tf", str(archive)], check=True, stdout=subprocess.DEVNULL, stderr=log, timeout=600)
                digest = hashlib.sha256()
                with archive.open("rb") as f:
                    while block := f.read(1024*1024):
                        digest.update(block)
                checkpoint["archive"] = archive.name
                checkpoint["sha256"] = digest.hexdigest()
                completed = outcome("succeeded", "verified", coverage="local_archive", bytes_verified=archive.stat().st_size, artifact=archive.name)
        except subprocess.TimeoutExpired:
            completed = outcome("unknown", "interrupted")
        except (OSError, ValueError, subprocess.CalledProcessError):
            completed = outcome("failed", "verification_failed")
    checkpoint["result"] = completed
    save(record, checkpoint)
    return completed


def main():
    os.umask(0o077)
    try:
        value = validate(json.loads(sys.stdin.buffer.read(4097)))
        STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (STATE / "lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            response = execute(value)
    except ValueError:
        response = outcome("failed", "disabled")
    except BlockingIOError:
        response = outcome("failed", "busy")
    except Exception:
        response = outcome("unknown", "interrupted")
    print(json.dumps(response))


if __name__ == "__main__":
    main()
