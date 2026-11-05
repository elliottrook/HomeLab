#!/usr/bin/env python3
"""Checkpoint and deploy the inert podcast request queue on TrueNAS."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen


SOURCE = Path("/tmp/aster-podcast-request-broker-stage")
TARGET = Path("/mnt/Media/appdata/aster-podcast-request-broker")
CONTAINER = "astertv-podcast-request-broker"
ABS = "unified-audiobookshelf-shadow"
IMAGE = "astertv-podcast-request-broker:sa-m5p1"
UID = GID = 65532


class InstallError(RuntimeError):
    pass


def run(command: tuple[str, ...], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def private_write(path: Path, data: bytes, *, uid: int = 0, gid: int = 0) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.fchown(stream.fileno(), uid, gid)


def docker(*arguments: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return run(("/usr/bin/docker",) + arguments, timeout)


def revoke(target: Path) -> None:
    script = target / "deploy/revoke_audiobookshelf_broker_key.js"
    docker("cp", str(script), ABS + ":/tmp/aster-podcast-revoke.js", timeout=30)
    docker("exec", "-e", "NODE_PATH=/app/node_modules", ABS,
           "node", "/tmp/aster-podcast-revoke.js", timeout=60)
    docker("exec", ABS, "rm", "-f", "/tmp/aster-podcast-revoke.js", timeout=30)


def main() -> int:
    if os.geteuid() != 0 or socket.gethostname() != "truenas":
        raise InstallError("TRUENAS_ROOT_REQUIRED")
    if (TARGET.exists() or not SOURCE.is_dir() or SOURCE.is_symlink()
            or docker("inspect", CONTAINER, timeout=30).returncode == 0):
        raise InstallError("INSTALL_STATE")
    required = {"Dockerfile", "contract.py", "persistence.py", "broker.py", "auth.py",
                "audiobookshelf.py", "server.py", "deploy/compose.yaml",
                "deploy/issue_audiobookshelf_broker_key.js",
                "deploy/revoke_audiobookshelf_broker_key.js"}
    if any(not (SOURCE / name).is_file() or (SOURCE / name).is_symlink() for name in required):
        raise InstallError("STAGE_INCOMPLETE")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    snapshot = "Media/appdata@aster-podcast-request-pre-" + stamp
    snapped = run(("/usr/sbin/zfs", "snapshot", snapshot), 60)
    if snapped.returncode != 0:
        raise InstallError("CHECKPOINT_FAILED")
    shutil.copytree(SOURCE, TARGET, symlinks=False)
    deploy = TARGET / "deploy"
    secrets_root = deploy / "secrets"
    state_root = deploy / "state"
    secrets_root.mkdir(mode=0o700)
    state_root.mkdir(mode=0o700)
    os.chown(secrets_root, UID, GID); os.chown(state_root, UID, GID)
    issue_script = TARGET / "deploy/issue_audiobookshelf_broker_key.js"
    issued_host = Path("/tmp/aster-podcast-broker-issued.json")
    if issued_host.exists():
        raise InstallError("CREDENTIAL_STAGE_EXISTS")
    key_created = False
    try:
        for command in (
            ("cp", str(issue_script), ABS + ":/tmp/aster-podcast-issue.js"),
            ("exec", "-e", "NODE_PATH=/app/node_modules", ABS,
             "node", "/tmp/aster-podcast-issue.js"),
            ("cp", ABS + ":/config/aster-podcast-broker-api-key.json", str(issued_host)),
        ):
            result = docker(*command, timeout=60)
            if result.returncode != 0:
                raise InstallError("AUDIOBOOKSHELF_KEY_ISSUE")
        key_created = True
        issued = json.loads(issued_host.read_text())
        if (set(issued) != {"api_key", "key_id", "name", "user_id_sha256", "username"}
                or issued["name"] != "AsterPodcastRequestBroker" or issued["username"] != "jason"
                or not isinstance(issued["api_key"], str) or len(issued["api_key"]) < 32):
            raise InstallError("AUDIOBOOKSHELF_KEY_SCHEMA")
        private_write(secrets_root / "audiobookshelf.key", issued["api_key"].encode(), uid=UID, gid=GID)
        private_write(deploy / "audiobookshelf-key-metadata.json",
                      (json.dumps({key: issued[key] for key in ("key_id", "name", "user_id_sha256", "username")},
                                  sort_keys=True) + "\n").encode())
        client_token = secrets.token_urlsafe(48)
        registry = {"schema": "aster-podcast-client-tokens.v1", "clients": [{
            "token_sha256": hashlib.sha256(client_token.encode()).hexdigest(),
            "client_id": "AsterTV-Jen", "profile_id": "jason", "enabled": True,
        }]}
        private_write(secrets_root / "client-tokens.json",
                      (json.dumps(registry, sort_keys=True) + "\n").encode(), uid=UID, gid=GID)
        client = {"schema": "aster-podcast-request-client.v1",
                  "server_url": "http://192.168.20.40:8790", "token": client_token,
                  "client_id": "AsterTV-Jen", "profile_id": "jason"}
        private_write(deploy / "client-stage.json", (json.dumps(client, sort_keys=True) + "\n").encode())
        client_token = ""
        for command in (
            ("exec", ABS, "rm", "-f", "/config/aster-podcast-broker-api-key.json",
             "/tmp/aster-podcast-issue.js"),
        ):
            if docker(*command, timeout=30).returncode != 0:
                raise InstallError("CREDENTIAL_STAGE_CLEANUP")
        issued_host.unlink()
        compose = str(deploy / "compose.yaml")
        checks = (
            ("compose", "-f", compose, "config", "--quiet"),
            ("compose", "-f", compose, "build", "--pull"),
            ("compose", "-f", compose, "up", "-d"),
        )
        for command in checks:
            result = docker(*command, timeout=600)
            if result.returncode != 0:
                raise InstallError("DOCKER_" + command[-1].upper().replace("-", "_"))
        deadline = time.time() + 90
        health = None
        while time.time() < deadline:
            try:
                health = json.load(urlopen("http://192.168.20.40:8790/health", timeout=3))
            except Exception:
                time.sleep(2)
                continue
            if health == {"state": "ready", "execution_enabled": False}:
                break
            time.sleep(2)
        else:
            raise InstallError("BROKER_HEALTH")
        image = docker("image", "inspect", IMAGE, "--format", "{{.Id}}", timeout=30)
        if image.returncode != 0 or not image.stdout.strip().startswith("sha256:"):
            raise InstallError("IMAGE_IDENTITY")
        manifest = {"schema": "aster-podcast-request-deployment.v1", "snapshot": snapshot,
                    "image": IMAGE, "image_id": image.stdout.strip(), "execution_enabled": False,
                    "client_stage": str(deploy / "client-stage.json")}
        private_write(deploy / "deployment.json", (json.dumps(manifest, sort_keys=True) + "\n").encode())
        print(json.dumps({"state": "installed-inert", "snapshot": snapshot,
                          "image_id": image.stdout.strip(), "execution_enabled": False,
                          "client_stage": str(deploy / "client-stage.json"),
                          "credential_output": False}, sort_keys=True))
        return 0
    except BaseException:
        compose = TARGET / "deploy/compose.yaml"
        if compose.exists():
            docker("compose", "-f", str(compose), "down", timeout=120)
        if key_created:
            revoke(TARGET)
        raise
    finally:
        if issued_host.exists():
            issued_host.unlink()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"state": "no_go", "code": str(error),
                          "credential_output": False}, sort_keys=True))
        raise SystemExit(1)
