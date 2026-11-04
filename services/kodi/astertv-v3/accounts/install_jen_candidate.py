#!/usr/bin/env python3
"""Checkpoint and install/rollback the isolated M2 candidate on AsterTV-Jen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


EXPECTED_HOST = "AsterTV-Jen"
KODI = Path("/storage/.kodi")
ADDON = KODI / "addons/script.asterprofiles.v3lab"
STATE = KODI / "userdata/addon_data/script.asterprofiles.v3lab"
KEYMAP = KODI / "userdata/keymaps/z-astertv-v3-m2-profile-gate.xml"
GUARD = Path("/storage/.aster-release/release_guard.py")
CHECKPOINT_ROOT = Path("/storage/.aster-checkpoints")
CHECKPOINT_FILES = (
    KODI / "userdata/profiles.xml",
    KODI / "userdata/guisettings.xml",
    KODI / "userdata/addon_data/skin.asterhome/settings.xml",
    KODI / "userdata/Database/Addons33.db",
    Path("/storage/.aster-release/accepted/accepted-manifest.json"),
    Path("/storage/.aster-policy/jellyfin_client_policy.py"),
)


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=2) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        payload = b""
        while True:
            block = connection.recv(65536)
            if not block:
                break
            payload += block
            try:
                json.loads(payload)
                break
            except json.JSONDecodeError:
                continue
    if not payload:
        raise RuntimeError("json-rpc-empty-response")
    response = json.loads(payload)
    if "error" in response:
        raise RuntimeError("json-rpc-error:" + str(response["error"].get("code")))
    return response.get("result")


def require_boundary():
    host = socket.gethostname()
    if host != EXPECTED_HOST:
        raise RuntimeError("wrong-target:" + host)
    if ADDON.exists() or STATE.exists() or KEYMAP.exists():
        raise RuntimeError("isolated-candidate-already-present")
    active = json_rpc("Player.GetActivePlayers")
    if active:
        raise RuntimeError("active-playback")
    completed = run("python3", str(GUARD), "verify", "--host", EXPECTED_HOST)
    report = json.loads(completed.stdout)
    if report.get("outcome") != "clean" or report.get("files") != 528:
        raise RuntimeError("release-guard-not-clean")


def checkpoint(identifier):
    destination = CHECKPOINT_ROOT / identifier
    if destination.exists():
        raise RuntimeError("checkpoint-already-exists")
    destination.mkdir(parents=True, mode=0o700)
    rows = []
    for source in CHECKPOINT_FILES:
        if not source.is_file():
            raise RuntimeError("checkpoint-source-missing:" + str(source))
        relative = source.relative_to("/")
        target = destination / "files" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        rows.append({"path": str(source), "bytes": source.stat().st_size, "sha256": sha256(source)})
    report = {
        "schema": 1,
        "kind": "astertv-v3-m2-jen-checkpoint",
        "host": EXPECTED_HOST,
        "candidate_addon_preexisting": False,
        "candidate_state_preexisting": False,
        "files": rows,
    }
    manifest = destination / "checkpoint.json"
    manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(manifest, 0o600)
    return destination, report


def validate_archive(archive, expected_sha):
    if sha256(archive) != expected_sha:
        raise RuntimeError("candidate-sha256-mismatch")
    allowed = {
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/addon.xml",
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/default.py",
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/service.py",
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/registry.py",
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/access_policy.py",
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/authority.py",
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/identity_resolver.py",
        "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab/synthetic-fixture.json",
        "astertv-v3-m2-jen/keymaps/z-astertv-v3-m2-profile-gate.xml",
        "astertv-v3-m2-jen/manifest.json",
    }
    with tarfile.open(archive, "r:gz") as bundle:
        names = set()
        for member in bundle.getmembers():
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or ".." in path.parts:
                raise RuntimeError("unsafe-candidate-member")
            names.add(member.name)
        if names != allowed:
            raise RuntimeError("candidate-member-set-mismatch")
        manifest = json.load(bundle.extractfile("astertv-v3-m2-jen/manifest.json"))
        if manifest.get("target") != EXPECTED_HOST or manifest.get("release") is not False:
            raise RuntimeError("candidate-manifest-boundary-failed")
        if manifest.get("client_capability_policy_included") is not False:
            raise RuntimeError("candidate-must-not-contain-client-policy")
    return manifest


def install(archive, expected_sha, identifier):
    require_boundary()
    manifest = validate_archive(archive, expected_sha)
    destination, checkpoint_report = checkpoint(identifier)
    run("systemctl", "stop", "kodi")
    try:
        with tempfile.TemporaryDirectory(prefix="astertv-v3-m2-", dir="/storage/.aster-staging") as temporary:
            with tarfile.open(archive, "r:gz") as bundle:
                bundle.extractall(temporary)
            source = Path(temporary) / "astertv-v3-m2-jen/addons/script.asterprofiles.v3lab"
            staging = ADDON.with_name("." + ADDON.name + ".installing")
            shutil.copytree(source, staging)
            for path in staging.rglob("*"):
                if path.is_file():
                    os.chmod(path, 0o644)
            os.replace(staging, ADDON)
            keymap_source = Path(temporary) / "astertv-v3-m2-jen/keymaps/z-astertv-v3-m2-profile-gate.xml"
            keymap_staging = KEYMAP.with_name("." + KEYMAP.name + ".installing")
            shutil.copy2(keymap_source, keymap_staging)
            os.chmod(keymap_staging, 0o644)
            os.replace(keymap_staging, KEYMAP)
        run("systemctl", "start", "kodi")
    except Exception:
        if ADDON.exists():
            shutil.rmtree(ADDON)
        KEYMAP.unlink(missing_ok=True)
        run("systemctl", "start", "kodi")
        raise
    print(json.dumps({
        "outcome": "installed",
        "target": EXPECTED_HOST,
        "candidate_sha256": expected_sha,
        "checkpoint": str(destination),
        "checkpoint_files": len(checkpoint_report["files"]),
        "candidate_kind": manifest["kind"],
    }, sort_keys=True))


def rollback(identifier):
    if socket.gethostname() != EXPECTED_HOST:
        raise RuntimeError("wrong-target")
    if json_rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    destination = CHECKPOINT_ROOT / identifier
    manifest = json.loads((destination / "checkpoint.json").read_text())
    if manifest.get("host") != EXPECTED_HOST:
        raise RuntimeError("checkpoint-host-mismatch")
    run("systemctl", "stop", "kodi")
    try:
        if ADDON.exists():
            shutil.rmtree(ADDON)
        if STATE.exists():
            shutil.rmtree(STATE)
        KEYMAP.unlink(missing_ok=True)
        for row in manifest["files"]:
            target = Path(row["path"])
            source = destination / "files" / target.relative_to("/")
            if sha256(source) != row["sha256"]:
                raise RuntimeError("checkpoint-drift:" + row["path"])
            shutil.copy2(source, target)
        run("systemctl", "start", "kodi")
    except Exception:
        run("systemctl", "start", "kodi")
        raise
    print(json.dumps({"outcome": "rolled-back", "target": EXPECTED_HOST,
                      "checkpoint": str(destination)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    install_parser = sub.add_parser("install")
    install_parser.add_argument("--archive", type=Path, required=True)
    install_parser.add_argument("--sha256", required=True)
    install_parser.add_argument("--checkpoint-id", required=True)
    rollback_parser = sub.add_parser("rollback")
    rollback_parser.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    if args.action == "install":
        install(args.archive, args.sha256, args.checkpoint_id)
    else:
        rollback(args.checkpoint_id)


if __name__ == "__main__":
    main()
