#!/usr/bin/env python3
"""Checkpoint, stage, apply, accept or roll back one AsterTV composition bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


CHECKPOINT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
ALLOWED_MODES = {0o600, 0o644, 0o700, 0o755}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(value, output, indent=2, sort_keys=True)
            output.write("\n"); output.flush(); os.fsync(output.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def safe_destination(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (not value.startswith("/storage/") or ".." in path.parts or
            path.as_posix() != value):
        raise ValueError("unsafe-install-destination")
    return path


def rooted(root: Path, destination: str) -> Path:
    return root / str(safe_destination(destination)).lstrip("/")


def load_bundle(path: Path, expected_sha256: str) -> tuple[dict, dict, dict[str, bytes]]:
    if sha256(path) != expected_sha256:
        raise ValueError("bundle-hash-mismatch")
    with tarfile.open(path, "r:gz") as archive:
        manifest = json.load(archive.extractfile("manifest.json"))
        guard = json.load(archive.extractfile("guard-contract.json"))
        if (manifest.get("kind") != "astertv-composition-bundle" or
                manifest.get("schema_version") != 1 or
                guard.get("kind") != "composition-guard-contract" or
                manifest.get("device_id") != guard.get("device_id") or
                manifest.get("composition_sha256") != guard.get("composition_sha256")):
            raise ValueError("bundle-contract-mismatch")
        rows = manifest.get("install_payloads")
        if not isinstance(rows, list):
            raise ValueError("bundle-install-contract-mismatch")
        contract_rows = [{key: row[key] for key in
                          ("overlay", "path", "sha256", "bytes", "mode")}
                         for row in rows]
        if contract_rows != guard.get("expected_payloads"):
            raise ValueError("bundle-install-contract-mismatch")
        payloads = {}
        destinations = set()
        for row in rows:
            destination = row["path"]
            safe_destination(destination)
            if destination in destinations:
                raise ValueError("duplicate-install-destination")
            destinations.add(destination)
            expected_archive = "install" + destination
            if row.get("archive_path") != expected_archive:
                raise ValueError("bundle-install-path-mismatch")
            member = archive.getmember(expected_archive)
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError("bundle-install-member-type")
            data = archive.extractfile(member).read()
            if (len(data) != row["bytes"] or
                    hashlib.sha256(data).hexdigest() != row["sha256"] or
                    int(row["mode"], 8) not in ALLOWED_MODES):
                raise ValueError("bundle-install-member-drift")
            payloads[destination] = data
    return manifest, guard, payloads


def plan(root: Path, manifest: dict) -> dict:
    rows = []
    for row in manifest["install_payloads"]:
        target = rooted(root, row["path"])
        if target.is_symlink():
            raise ValueError("live-symlink")
        if not target.exists():
            state = "missing"
        elif not target.is_file():
            raise ValueError("live-non-file")
        elif (target.stat().st_size == row["bytes"] and sha256(target) == row["sha256"]
              and stat.S_IMODE(target.stat().st_mode) == int(row["mode"], 8)):
            state = "matching"
        else:
            state = "replace"
        rows.append({"path": row["path"], "state": state})
    return {state: sum(row["state"] == state for row in rows)
            for state in ("matching", "missing", "replace")} | {"rows": rows}


def checkpoint(root: Path, manifest: dict, checkpoint_root: Path,
               checkpoint_id: str, systemd_state: list[dict] | None = None) -> Path:
    if not CHECKPOINT_RE.fullmatch(checkpoint_id):
        raise ValueError("checkpoint-id")
    target = checkpoint_root / checkpoint_id
    if target.exists():
        raise ValueError("checkpoint-exists")
    checkpoint_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{checkpoint_id}-", dir=checkpoint_root))
    rows = []
    try:
        for row in manifest["install_payloads"]:
            live = rooted(root, row["path"])
            if live.is_symlink():
                raise ValueError("checkpoint-symlink")
            record = {"path": row["path"], "existed": live.is_file()}
            if live.exists() and not live.is_file():
                raise ValueError("checkpoint-non-file")
            if live.is_file():
                saved = temporary / "files" / row["path"].lstrip("/")
                saved.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                shutil.copy2(live, saved)
                record.update(sha256=sha256(live), bytes=live.stat().st_size,
                              mode=format(stat.S_IMODE(live.stat().st_mode), "04o"))
            rows.append(record)
        recovery = []
        for name in ("accepted", "accepted.previous"):
            live = root / "storage/.aster-release" / name
            record = {"name": name, "existed": live.is_dir()}
            if live.exists() and (not live.is_dir() or live.is_symlink()):
                raise ValueError("accepted-state-type")
            if live.is_dir():
                shutil.copytree(live, temporary / "recovery" / name)
            recovery.append(record)
        journal = {"schema_version": 1, "kind": "astertv-composition-checkpoint",
                   "device_id": manifest["device_id"],
                   "composition_sha256": manifest["composition_sha256"],
                   "checkpoint_id": checkpoint_id, "status": "checkpointed",
                   "files": rows, "recovery": recovery,
                   "systemd": systemd_state or []}
        atomic_json(temporary / "checkpoint.json", journal)
        os.replace(temporary, target)
        return target
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def stage(root: Path, manifest: dict, payloads: dict[str, bytes],
          stage_root: Path, checkpoint_id: str) -> Path:
    target = stage_root / checkpoint_id
    if target.exists():
        raise ValueError("stage-exists")
    stage_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{checkpoint_id}-", dir=stage_root))
    try:
        for row in manifest["install_payloads"]:
            output = temporary / row["path"].lstrip("/")
            output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            output.write_bytes(payloads[row["path"]])
            os.chmod(output, int(row["mode"], 8))
            if sha256(output) != row["sha256"]:
                raise ValueError("staged-payload-drift")
        os.replace(temporary, target)
        return target
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def install(root: Path, manifest: dict, staged: Path) -> list[str]:
    changed = []
    for row in manifest["install_payloads"]:
        source = staged / row["path"].lstrip("/")
        target = rooted(root, row["path"])
        if target.is_symlink() or not source.is_file() or sha256(source) != row["sha256"]:
            raise ValueError("install-precondition")
        clean = (target.is_file() and target.stat().st_size == row["bytes"] and
                 sha256(target) == row["sha256"] and
                 stat.S_IMODE(target.stat().st_mode) == int(row["mode"], 8))
        if clean:
            continue
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(source.read_bytes()); output.flush(); os.fsync(output.fileno())
            os.chmod(temporary, int(row["mode"], 8))
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        changed.append(row["path"])
    return changed


def restore(root: Path, checkpoint_path: Path) -> dict:
    journal_path = checkpoint_path / "checkpoint.json"
    journal = json.loads(journal_path.read_text())
    restored = []
    for row in journal["files"]:
        live = rooted(root, row["path"])
        if live.is_symlink():
            raise ValueError("rollback-symlink")
        if row["existed"]:
            saved = checkpoint_path / "files" / row["path"].lstrip("/")
            if (not saved.is_file() or sha256(saved) != row["sha256"] or
                    saved.stat().st_size != row["bytes"]):
                raise ValueError("checkpoint-payload-drift")
            live.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            shutil.copy2(saved, live)
            os.chmod(live, int(row["mode"], 8))
        elif live.exists():
            if not live.is_file():
                raise ValueError("rollback-new-path-type")
            live.unlink()
        restored.append(row["path"])
    release_root = root / "storage/.aster-release"
    for row in journal["recovery"]:
        live = release_root / row["name"]
        if live.exists():
            if not live.is_dir() or live.is_symlink():
                raise ValueError("rollback-accepted-type")
            shutil.rmtree(live)
        if row["existed"]:
            shutil.copytree(checkpoint_path / "recovery" / row["name"], live)
    journal["status"] = "rolled-back"
    atomic_json(journal_path, journal)
    return {"outcome": "rolled-back", "files": len(restored)}


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def systemctl_state(unit: str, property_name: str) -> str:
    result = subprocess.run(["systemctl", f"is-{property_name}", unit],
                            check=False, capture_output=True, text=True)
    return result.stdout.strip() or "unknown"


def systemd_assertion_target(assertion: dict) -> tuple[str, str]:
    key, desired = assertion["key"], assertion["expected"]
    if key.endswith(".masked") and isinstance(desired, bool):
        return key.removesuffix(".masked") + ".service", "masked"
    return key, "unit-state"


def collect_systemd_state(guard: dict) -> list[dict]:
    rows = []
    for assertion in guard.get("expected_assertions", []):
        if assertion.get("authority") != "systemd":
            continue
        unit, assertion_type = systemd_assertion_target(assertion)
        rows.append({"unit": unit, "assertion_type": assertion_type,
                     "desired": assertion["expected"],
                     "enabled": systemctl_state(unit, "enabled"),
                     "active": systemctl_state(unit, "active")})
    return rows


def reconcile_systemd(guard: dict) -> None:
    for assertion in guard.get("expected_assertions", []):
        if assertion.get("authority") != "systemd":
            continue
        unit, assertion_type = systemd_assertion_target(assertion)
        desired = assertion["expected"]
        if assertion_type == "masked" and desired is True:
            run(["systemctl", "mask", unit])
        elif assertion_type == "masked" and desired is False:
            run(["systemctl", "unmask", unit])
        elif desired == "enabled":
            run(["systemctl", "enable", unit])
        elif desired == "enabled-active":
            run(["systemctl", "enable", "--now", unit])
        elif desired == "disabled":
            run(["systemctl", "disable", unit])
        elif desired == "disabled-inactive":
            run(["systemctl", "disable", "--now", unit])
        else:
            raise ValueError("unsupported-systemd-assertion")


def restore_systemd(rows: list[dict]) -> None:
    for row in rows:
        unit = row["unit"]
        if row["enabled"] == "not-found":
            continue
        if row["enabled"] == "masked":
            run(["systemctl", "mask", unit])
        elif row["enabled"] == "enabled":
            run(["systemctl", "enable", unit])
        elif row["enabled"] == "disabled":
            run(["systemctl", "disable", unit])
        else:
            raise ValueError("unsupported-checkpointed-unit-state")
        if row["active"] == "active":
            run(["systemctl", "start", unit])
        elif row["active"] in {"inactive", "failed"}:
            run(["systemctl", "stop", unit])
        else:
            raise ValueError("unsupported-checkpointed-active-state")


def suspend_guard() -> None:
    """Stop Kodi and remove the persistent boot edge before candidate start."""
    run(["systemctl", "stop", "kodi.service"])
    run(["systemctl", "disable", "astertv-release-guard.service"])
    run(["systemctl", "daemon-reload"])


def resume_guard() -> None:
    """Restore the boot edge, reload systemd and start Kodi."""
    run(["systemctl", "enable", "astertv-release-guard.service"])
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "start", "kodi.service"])


def idle_players() -> bool:
    request = b'{"jsonrpc":"2.0","method":"Player.GetActivePlayers","id":1}\n'
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall(request)
        response = connection.recv(8192)
    return json.loads(response.decode())["result"] == []


def update_status(checkpoint_path: Path, status_value: str, **fields) -> None:
    path = checkpoint_path / "checkpoint.json"
    journal = json.loads(path.read_text())
    journal.update(status=status_value, **fields)
    atomic_json(path, journal)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "apply", "accept", "rollback"))
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--bundle-sha256")
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--checkpoint-root", type=Path,
                        default=Path("/storage/.aster-checkpoints"))
    parser.add_argument("--stage-root", type=Path, default=Path("/storage/.aster-deploy"))
    parser.add_argument("--offline", action="store_true",
                        help="test-only: do not control Kodi/systemd")
    args = parser.parse_args(argv)
    checkpoint_path = args.checkpoint_root / args.checkpoint_id
    if args.action == "rollback":
        if not args.offline:
            suspend_guard()
        result = restore(args.root, checkpoint_path)
        if not args.offline:
            journal = json.loads((checkpoint_path / "checkpoint.json").read_text())
            restore_systemd(journal.get("systemd", []))
            resume_guard()
        print(json.dumps(result, sort_keys=True)); return 0
    if args.action == "accept":
        journal = json.loads((checkpoint_path / "checkpoint.json").read_text())
        if not args.offline:
            if not idle_players():
                raise ValueError("playback-active")
            suspend_guard()
            run(["/usr/bin/python3", "/storage/.aster-release/release_guard.py",
                 "snapshot", "--host", socket.gethostname()])
            resume_guard()
        update_status(checkpoint_path, "accepted",
                      accepted_composition=journal["composition_sha256"])
        print(json.dumps({"outcome": "accepted", "device_id": journal["device_id"]},
                         sort_keys=True)); return 0
    if not args.bundle or not args.bundle_sha256:
        parser.error("--bundle and --bundle-sha256 are required")
    manifest, guard, payloads = load_bundle(args.bundle, args.bundle_sha256)
    if not args.offline and socket.gethostname() != guard["hostname"]:
        raise ValueError("device-hostname-mismatch")
    result = plan(args.root, manifest)
    if args.action == "preflight":
        print(json.dumps({"outcome": "ready", "device_id": manifest["device_id"],
                          "composition_sha256": manifest["composition_sha256"],
                          **{key: result[key] for key in ("matching", "missing", "replace")}},
                         sort_keys=True)); return 0
    if not args.offline and not idle_players():
        raise ValueError("playback-active")
    systemd_state = [] if args.offline else collect_systemd_state(guard)
    checkpoint_path = checkpoint(args.root, manifest, args.checkpoint_root,
                                 args.checkpoint_id, systemd_state)
    staged = stage(args.root, manifest, payloads, args.stage_root, args.checkpoint_id)
    try:
        if not args.offline:
            suspend_guard()
        changed = install(args.root, manifest, staged)
        if not args.offline:
            reconcile_systemd(guard)
            run(["systemctl", "daemon-reload"])
            run(["systemctl", "start", "kodi.service"])
        update_status(checkpoint_path, "candidate-running", changed=changed,
                      guard_disabled=not args.offline)
    except Exception:
        restore(args.root, checkpoint_path)
        if not args.offline:
            restore_systemd(systemd_state)
            resume_guard()
        raise
    print(json.dumps({"outcome": "candidate-running", "changed": len(changed),
                      "checkpoint": str(checkpoint_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
