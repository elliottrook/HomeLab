#!/usr/bin/env python3
"""Mac outbound worker. Fixed adapters; no remote command or path supplied by Aster."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import tarfile
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CONFIG_TARGETS = ("opnsense", "arista", "proxmox", "nut", "observability", "video-archiver")
GUEST_TARGETS = ("guest-104", "guest-109", "guest-111", "guest-113", "guest-116")
REQUIRED = {
    "arista": ("running-config.txt", "startup-config.txt", "version.txt", "inventory.txt", "interfaces-status.txt", "vlan.txt", "environment.txt"),
    "nut": ("ups.conf", "nut.conf", "upsd.users", "upsmon.conf", "sshd-hardening.conf", "network-interfaces.txt", "hostnamectl.txt"),
    "video-archiver": ("config.json", ".env", "run-scheduled.sh"),
    "proxmox": ("proxmox-host-config.tar.gz", "proxmox-host-config.tar.gz.sha256", "pve-version.txt", "lxc-list.txt", "vm-list.txt", "storage-status.txt", "block-devices.txt", "network-addresses.txt"),
    "observability": ("observability-config.tar.gz", "observability-config.tar.gz.sha256"),
}


def result(state, code, **evidence):
    return {"state": state, "code": code, "coverage": "none", **evidence}


def write_json(path, value):
    candidate = path.with_suffix(".tmp")
    with candidate.open("w") as f:
        json.dump(value, f)
        f.flush()
        os.fsync(f.fileno())
    candidate.replace(path)


def run(command, output, timeout, env=None):
    """Private logs only. Never return process output as an API error."""
    with output.open("wb") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, start_new_session=True, env=env)
        try:
            return process.wait(timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            return None


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_archive(path, required):
    names = set()
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            names.add(member.name.rstrip("/"))
            if member.isfile():
                f = archive.extractfile(member)
                size = 0
                while chunk := f.read(1024*1024):
                    size += len(chunk)
                if size != member.size:
                    raise ValueError("Truncated archive")
        if not set(required) <= names:
            raise ValueError("Missing archive entries")
        if "var/lib/grafana/grafana.db" in names:
            # Work on a disposable copy, never open the production database.
            with tempfile.TemporaryDirectory() as directory:
                database = Path(directory) / "grafana.db"
                with database.open("wb") as out:
                    f = archive.extractfile("var/lib/grafana/grafana.db")
                    while chunk := f.read(1024*1024):
                        out.write(chunk)
                with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
                    if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                        raise ValueError("Database integrity failed")


def verify_config(target, root, started):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Invalid backup directory")
    if target == "opnsense":
        candidates = list(root.glob("opnsense-config-*.xml"))
        newest = max(candidates, key=lambda p: p.stat().st_mtime)
        files = [newest, newest.with_suffix(newest.suffix + ".sha256")]
    else:
        candidates = [p for p in root.iterdir() if p.is_dir() and not p.is_symlink()]
        newest = max(candidates, key=lambda p: p.stat().st_mtime)
        files = [newest / name for name in REQUIRED[target]]
    for path in files:
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0 or path.stat().st_mtime < started-2:
            raise ValueError("Missing, stale or empty artifact")
        path.chmod(0o600)
    if target == "opnsense":
        if ET.parse(files[0]).getroot().tag != "opnsense":
            raise ValueError("Invalid OPNsense export")
    if target == "video-archiver":
        if not isinstance(json.loads(files[0].read_text()), dict):
            raise ValueError("Invalid archiver configuration")
    for path in files:
        if path.suffix == ".sha256":
            archive = Path(str(path)[:-7])
            expected = path.read_text().split()[0]
            if expected != sha256(archive):
                raise ValueError("Checksum mismatch")
        if path.name.endswith(".tar.gz"):
            required = ("etc/pve", "etc/network/interfaces", "usr/local/sbin/aster-lab-guest", "etc/sudoers.d/aster-lab-backup", "var/lib/aster-lab-guest") if target == "proxmox" else ("etc/prometheus/prometheus.yml", "etc/grafana/grafana.ini", "var/lib/grafana/grafana.db", "var/lib/grafana/dashboards/homelab-overview.json")
            verify_archive(path, required)
    # Manifest for config sets, retained privately alongside artifacts.
    manifest = {p.name: sha256(p) for p in files}
    write_json(files[0].parent / (files[0].name + ".verified.json"), manifest)
    return sum(p.stat().st_size for p in files)


def snapshot_custody(custody, home):
    """Protected recovery bundle, picked up by the existing TrueNAS Mac pull."""
    destination = home / "lab/private-backups/aster-lab-operations"
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.chmod(0o700)
    name = time.strftime("%Y-%m-%d_%H-%M-%S") + "-" + os.urandom(4).hex() + ".tar.gz"
    temporary = destination / (name + ".partial")
    paths = ["worker.py", "worker.json", "guest_ed25519", "guest_ed25519.pub",
             "installation.json", "toolkit", "state/capacity-reservations.json"]
    with tarfile.open(temporary, "w:gz") as archive:
        for relative in paths:
            path = custody / relative
            if path.exists() and not path.is_symlink():
                archive.add(path, arcname=relative)
    temporary.chmod(0o600)
    verify_archive(temporary, ["worker.py", "worker.json", "toolkit"])
    final = destination / name
    temporary.replace(final)
    write_json(final.with_suffix(final.suffix + ".verified.json"), {"sha256": sha256(final), "bytes": final.stat().st_size})
    return final.stat().st_size


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class Worker:
    def __init__(self, config):
        self.config = config
        self.repo = Path(config["repository"]).resolve()
        self.state = Path(config["state"]).resolve()
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.pending = self.state / "pending.json"
        self.home = Path(config["home"]).resolve()
        self.enabled = set(config.get("targets", []))
        if config["url"] != "https://aster.elliottrook.com":
            raise ValueError("Unapproved broker URL")
        # Use pinned deployment copy, never the live working tree.
        if not (self.repo / "scripts/doctor.sh").is_file():
            raise ValueError("Missing deployment scripts")
        self.env = dict(os.environ, HOME=str(self.home), HOMELAB_REPO=str(self.repo), HOMELAB_GIT_REPO=str(self.home / "lab/homelab"), PATH=str(self.state / "bin") + ":/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin")
        bindir = self.state / "bin"
        bindir.mkdir(exist_ok=True, mode=0o700)
        for command in ("ssh", "scp"):
            wrapper = bindir / command
            wrapper.write_text(f'#!/bin/sh\nexec /usr/bin/{command} -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=15 -o ServerAliveCountMax=2 "$@"\n')
            wrapper.chmod(0o700)

    def call(self, path, payload):
        request = urllib.request.Request(self.config["url"] + path,
                    data=json.dumps(payload).encode(), headers={"Content-Type": "application/json",
                    "Authorization": "Bearer " + self.config["worker_key"]}, method="POST")
        # No proxy environment forwarding of the private worker credential.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=20) as response:
            return json.loads(response.read(65536))

    def truenas_capacity(self, job):
        """Reserve for archives not yet seen at the scheduled mirror destination.

        Size matching here only releases capacity reservations; it never claims
        checksum verification or off-host recovery coverage to Aster.
        """
        ledger_path = self.state / "capacity-reservations.json"
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
        def remote(command):
            response = subprocess.run(["/usr/bin/ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "truenas", command],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
            if not re.fullmatch(rb"[0-9]+\s*", response.stdout):
                raise ValueError("Invalid capacity result")
            return int(response.stdout)
        try:
            for jid, reservation in list(ledger.items()):
                name = reservation.get("artifact", "")
                if not re.fullmatch(r"vzdump-lxc-(104|109|111|113|116)-[0-9_\-]+\.tar\.zst", name):
                    continue
                try:
                    size = remote("stat -c %s /mnt/Media/backup/homelab-proxmox-guests/" + name)
                    if size == reservation["bytes_verified"]:
                        del ledger[jid]
                except (OSError, ValueError, subprocess.SubprocessError):
                    pass
            free = remote("zfs get -H -p -o value available Media/backup")
            outstanding = sum(r["reserved"] for r in ledger.values())
            needed = 256 * 1024**3 if job["target"] in GUEST_TARGETS else 10 * 1024**3
            # A shared-pool reserve, not an attempt to infer filesystem capacity
            # from raw zpool free space.
            if free - outstanding < needed + 256 * 1024**3:
                return False
            if job["target"] in GUEST_TARGETS:
                ledger[job["id"]] = {"reserved": needed}
            write_json(ledger_path, ledger)
            return True
        except (OSError, ValueError, subprocess.SubprocessError):
            return False

    def execute(self, job):
        target = job["target"]
        if target not in self.enabled:
            return result("failed", "disabled")
        log = self.state / "last-operation.log"
        if target == "doctor":
            code = run(["/bin/bash", str(self.repo / "scripts/doctor.sh")], log, 600, self.env)
            if code is None:
                return result("unknown", "interrupted")
            text = log.read_text(errors="replace")
            counts = []
            for key in ("Passed", "Warnings", "Failed"):
                match = re.search(rf"{key}:\s+(\d+)", text)
                if not match:
                    return result("failed", "adapter_failed")
                counts.append(int(match[1]))
            if code not in (0, 1):
                return result("failed", "adapter_failed")
            checks = []
            for line in text.splitlines():
                line = re.sub(r"\x1b\[[0-9;]*m", "", line)
                match = re.match(r"^([🟢🟡🔴])\s+(.+)$", line)
                if not match or re.match(r"(?:Passed|Warnings|Failed):", match[2]):
                    continue
                summary = match[2][:240]
                if re.search(r"password|secret|token|credential|bearer|BEGIN |/(?:Users|etc|root|var|mnt)/|[A-Za-z0-9_+/=-]{40,}|[\x00-\x1f]", summary, re.I):
                    summary = "Details withheld; inspect the private operator report."
                checks.append({"status": {"🟢":"pass", "🟡":"warn", "🔴":"fail"}[match[1]], "summary": summary})
            checks = list({(c["status"], c["summary"]): c for c in checks}.values())
            checks.sort(key=lambda c: {"fail":0,"warn":1,"pass":2}[c["status"]])
            return result("succeeded", "checks_complete", coverage="diagnostic", passed=counts[0], warnings=counts[1], failures=counts[2], checks=checks[:32])
        if target != "doctor" and not self.truenas_capacity(job):
            return result("failed", "low_space")
        if target in GUEST_TARGETS:
            # Dedicated SSH identity is forced to a fixed server-side helper.
            # Only target enum is passed on stdin; never shell interpolation.
            with log.open("wb") as out:
                try:
                    proc = subprocess.run(["/usr/bin/ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=2", "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none", "-T", "-i", self.config["guest_key"], "ai-lab-backup@192.168.50.10"],
                        input=json.dumps({"target": target, "id": job["id"]}).encode(), stdout=subprocess.PIPE, stderr=out, timeout=5400)
                    response = json.loads(proc.stdout) if len(proc.stdout) < 4096 else {}
                    if response.get("state") not in ("succeeded", "failed", "unknown"):
                        raise ValueError()
                    artifact = response.pop("artifact", None)
                    if artifact is not None:
                        if not re.fullmatch(r"vzdump-lxc-" + target.removeprefix("guest-") + r"-[0-9_\-]+\.tar\.zst", artifact):
                            raise ValueError()
                        ledger_path = self.state / "capacity-reservations.json"
                        ledger = json.loads(ledger_path.read_text())
                        ledger[job["id"]].update(artifact=artifact, bytes_verified=response["bytes_verified"], reserved=max(1024**3, int(response["bytes_verified"] * 1.2)))
                        write_json(ledger_path, ledger)
                    elif response.get("state") == "failed" and response.get("code") in {"busy", "low_space", "disabled"}:
                        ledger_path = self.state / "capacity-reservations.json"
                        ledger = json.loads(ledger_path.read_text())
                        ledger.pop(job["id"], None)
                        write_json(ledger_path, ledger)
                    return response
                except (subprocess.TimeoutExpired, ValueError, OSError):
                    return result("unknown", "interrupted")
        if target not in CONFIG_TARGETS:
            return result("failed", "disabled")
        backup_root = self.home / "lab/private-backups"
        # Reserve 20 GiB, including room for a bounded config export.
        stats = os.statvfs(backup_root)
        if stats.f_bavail * stats.f_frsize < 20 * 1024**3:
            return result("failed", "low_space")
        # Existing scheduled launcher has no shared lock. Detect its active
        # scripts and refuse this run; schedule exclusion below covers the race.
        processes = subprocess.run(["/bin/ps", "-axo", "command="], capture_output=True, text=True, check=True).stdout
        if any(f"/scripts/backup/{name}.sh" in processes for name in CONFIG_TARGETS):
            return result("failed", "busy")
        local = time.localtime()
        if local.tm_wday == 6 and 5 <= local.tm_hour < 8:
            return result("failed", "busy")
        # Partial exports stay outside the tree consumed by Doctor/TrueNAS.
        # Publish the entire validated set with one same-filesystem rename.
        # Staging must not be inside the published/pulled backup tree.
        staging_parent = self.home / "lab/.aster-backup-staging"
        staging_parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if staging_parent.stat().st_dev != backup_root.stat().st_dev:
            return result("failed", "adapter_failed")
        with tempfile.TemporaryDirectory(prefix="export-", dir=staging_parent) as staging:
            started = time.time()
            env = dict(self.env, HOMELAB_BACKUP_ROOT=staging)
            code = run(["/bin/bash", str(self.repo / f"scripts/backup/{target}.sh")], log, 600, env)
            if code is None:
                return result("unknown", "interrupted")
            if code != 0:
                return result("failed", "adapter_failed")
            source = Path(staging) / target
            try:
                total = verify_config(target, source, started)
                parent = backup_root / target
                parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                destination = parent / ("aster-" + job["id"])
                if destination.exists():
                    return result("unknown", "interrupted")
                source.rename(destination)
            except (OSError, ValueError, ET.ParseError, tarfile.TarError, sqlite3.Error):
                return result("failed", "verification_failed")
        return result("succeeded", "verified", coverage="config_export", bytes_verified=total)

    def tick(self):
        if self.pending.exists():
            pending = json.loads(self.pending.read_text())
            if "result" not in pending:
                # Process died after claim: cannot know whether it ran. Fail safe.
                pending["result"] = result("unknown", "interrupted")
                write_json(self.pending, pending)
        else:
            job = self.call("/v1/lab/worker/claim", {})["job"]
            if job is None:
                return
            if (not isinstance(job, dict) or set(job) != {"id", "target", "lease"}
                    or not isinstance(job["id"], str) or not re.fullmatch(r"[a-f0-9]{32}", job["id"])
                    or not isinstance(job["lease"], str) or not re.fullmatch(r"[a-f0-9]{64}", job["lease"])
                    or job["target"] not in ("doctor", *CONFIG_TARGETS, *GUEST_TARGETS)):
                raise ValueError("Invalid worker claim")
            pending = dict(job)
            write_json(self.pending, pending)
            try:
                pending["result"] = self.execute(job)
            except Exception:
                pending["result"] = result("unknown", "interrupted")
            write_json(self.pending, pending)
        # Retry delivery, never execution. Lease remains only in private files.
        self.call(f"/v1/lab/worker/jobs/{pending['id']}/complete",
                  {"lease": pending["lease"], "result": pending["result"]})
        self.pending.unlink()
        snapshot_custody(self.state.parent, self.home)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    if args.config.is_symlink() or args.config.stat().st_mode & 0o077:
        raise SystemExit("Worker config must be a private regular file")
    worker = Worker(json.loads(args.config.read_text()))
    with (worker.state / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        while True:
            try:
                worker.tick()
            except Exception:
                # Credentials, private backup paths and server bodies stay out of logs.
                print("Lab worker unavailable; will retry safely", flush=True)
            if args.once:
                break
            time.sleep(15)


if __name__ == "__main__":
    main()
