#!/usr/bin/env python3
"""Checkpoint, migrate and roll back Jen's isolated profile authority."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


EXPECTED_HOST = "AsterTV-Jen"
KODI = Path("/storage/.kodi")
ADDON = KODI / "addons/script.asterprofiles.v3lab"
STATE = KODI / "userdata/addon_data/script.asterprofiles.v3lab"
PROFILES = STATE / "profiles.json"
AUTHORITY = STATE / "authority.json"
KEYMAP = KODI / "userdata/keymaps/z-astertv-v3-m2-profile-gate.xml"
GUARD = Path("/storage/.aster-release/release_guard.py")
ACCEPTED = Path("/storage/.aster-release/accepted/accepted-manifest.json")
POLICY = Path("/storage/.aster-policy/jellyfin_client_policy.py")
CHECKPOINT_ROOT = Path("/storage/.aster-checkpoints")
ARCHIVE_ROOT = "astertv-v3-m2-jen"
ARCHIVE_FILES = {
    "addons/script.asterprofiles.v3lab/addon.xml",
    "addons/script.asterprofiles.v3lab/default.py",
    "addons/script.asterprofiles.v3lab/service.py",
    "addons/script.asterprofiles.v3lab/registry.py",
    "addons/script.asterprofiles.v3lab/access_policy.py",
    "addons/script.asterprofiles.v3lab/authority.py",
    "addons/script.asterprofiles.v3lab/identity_resolver.py",
    "addons/script.asterprofiles.v3lab/synthetic-fixture.json",
    "keymaps/z-astertv-v3-m2-profile-gate.xml",
    "manifest.json",
}


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_rpc(method):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=2) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        payload = connection.recv(65536)
    response = json.loads(payload)
    if "error" in response:
        raise RuntimeError("json-rpc-error")
    return response.get("result")


def require_idle_clean():
    if socket.gethostname() != EXPECTED_HOST:
        raise RuntimeError("wrong-target")
    if json_rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    result = json.loads(run("python3", str(GUARD), "verify", "--host", EXPECTED_HOST).stdout)
    if result.get("outcome") != "clean" or result.get("files") != 528:
        raise RuntimeError("release-guard-not-clean")


def validate_archive(archive, expected_sha):
    if sha256(archive) != expected_sha:
        raise RuntimeError("candidate-sha256-mismatch")
    with tarfile.open(archive, "r:gz") as bundle:
        names = set()
        for member in bundle.getmembers():
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or ".." in path.parts:
                raise RuntimeError("unsafe-candidate-member")
            if not member.name.startswith(ARCHIVE_ROOT + "/"):
                raise RuntimeError("candidate-root-mismatch")
            names.add(member.name[len(ARCHIVE_ROOT) + 1:])
        if names != ARCHIVE_FILES:
            raise RuntimeError("candidate-member-set-mismatch")
        manifest = json.load(bundle.extractfile(ARCHIVE_ROOT + "/manifest.json"))
        if (manifest.get("target") != EXPECTED_HOST or manifest.get("release") is not False
                or manifest.get("client_capability_policy_included") is not False):
            raise RuntimeError("candidate-boundary-failed")
    return manifest


def _copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def checkpoint(identifier):
    destination = CHECKPOINT_ROOT / identifier
    if destination.exists():
        raise RuntimeError("checkpoint-already-exists")
    if not ADDON.is_dir() or not STATE.is_dir() or not KEYMAP.is_file():
        raise RuntimeError("r6-candidate-missing")
    destination.mkdir(parents=True, mode=0o700)
    sources = (ADDON, STATE, KEYMAP, ACCEPTED, POLICY)
    rows = []
    for source in sources:
        target = destination / "files" / source.relative_to("/")
        _copy(source, target)
        if source.is_file():
            rows.append({"path": str(source), "sha256": sha256(source)})
        else:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    rows.append({"path": str(path), "sha256": sha256(path)})
    report = {"schema": 1, "kind": "astertv-v3-m2-jen-authority-checkpoint",
              "host": EXPECTED_HOST, "files": rows}
    manifest = destination / "checkpoint.json"
    manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(manifest, 0o600)
    return destination


def restore(destination):
    report = json.loads((destination / "checkpoint.json").read_text())
    if report.get("host") != EXPECTED_HOST:
        raise RuntimeError("checkpoint-host-mismatch")
    for row in report["files"]:
        source = destination / "files" / Path(row["path"]).relative_to("/")
        if not source.is_file() or sha256(source) != row["sha256"]:
            raise RuntimeError("checkpoint-drift")
    for target in (ADDON, STATE):
        if target.exists():
            shutil.rmtree(target)
    KEYMAP.unlink(missing_ok=True)
    for source in (ADDON, STATE, KEYMAP, ACCEPTED, POLICY):
        saved = destination / "files" / source.relative_to("/")
        _copy(saved, source)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def migrate(archive, expected_sha, identifier, admin_name, profile_id):
    require_idle_clean()
    validate_archive(archive, expected_sha)
    destination = checkpoint(identifier)
    run("systemctl", "stop", "kodi")
    try:
        with tempfile.TemporaryDirectory(prefix="astertv-v3-m2-authority-", dir="/storage/.aster-staging") as temporary:
            temporary = Path(temporary)
            with tarfile.open(archive, "r:gz") as bundle:
                bundle.extractall(temporary)
            root = temporary / ARCHIVE_ROOT
            source_addon = root / "addons/script.asterprofiles.v3lab"
            sys.path.insert(0, str(source_addon))
            registry = load_module("migrated_registry", source_addon / "registry.py")
            authority_module = load_module("migrated_authority", source_addon / "authority.py")
            config = {"schema": 1, "recovery_admin_display_name": admin_name,
                      "profile_id": profile_id}
            migrated = authority_module.build_registry(config, now())
            shutil.rmtree(ADDON)
            staging = ADDON.with_name("." + ADDON.name + ".migrating")
            shutil.copytree(source_addon, staging)
            for path in staging.rglob("*"):
                if path.is_file():
                    os.chmod(path, 0o644)
            os.replace(staging, ADDON)
            keymap_source = root / "keymaps/z-astertv-v3-m2-profile-gate.xml"
            shutil.copy2(keymap_source, KEYMAP)
            os.chmod(KEYMAP, 0o644)
            registry._atomic_write(
                AUTHORITY, (json.dumps(config, indent=2, sort_keys=True) + "\n").encode()
            )
            registry.store(PROFILES, migrated)
        run("systemctl", "start", "kodi")
    except Exception:
        restore(destination)
        run("systemctl", "start", "kodi")
        raise
    print(json.dumps({"outcome": "migrated", "target": EXPECTED_HOST,
                      "candidate_sha256": expected_sha, "checkpoint": str(destination),
                      "active_role": "guest", "enabled_services": 3,
                      "credential_output": False}, sort_keys=True))


def rollback(identifier):
    require_idle_clean()
    destination = CHECKPOINT_ROOT / identifier
    run("systemctl", "stop", "kodi")
    try:
        restore(destination)
        run("systemctl", "start", "kodi")
    except Exception:
        run("systemctl", "start", "kodi")
        raise
    print(json.dumps({"outcome": "rolled-back", "target": EXPECTED_HOST,
                      "checkpoint": str(destination)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)
    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--archive", type=Path, required=True)
    migrate_parser.add_argument("--sha256", required=True)
    migrate_parser.add_argument("--checkpoint-id", required=True)
    migrate_parser.add_argument("--admin-name", required=True)
    migrate_parser.add_argument("--profile-id", required=True)
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    if args.action == "migrate":
        migrate(args.archive, args.sha256, args.checkpoint_id,
                args.admin_name, args.profile_id)
    else:
        rollback(args.checkpoint_id)


if __name__ == "__main__":
    main()
