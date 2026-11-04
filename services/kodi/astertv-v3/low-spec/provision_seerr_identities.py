#!/usr/bin/env python3
"""Issue distinct AsterTV-Jen Seerr/acquisition tokens and deploy multi-token auth.

Run as root on the TrueNAS Docker host. Tokens remain in the protected secrets
directory and are never printed.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
from typing import Optional
import urllib.error
import urllib.request

import yaml


CONTAINER = "unified-aster-seerr-broker"
SERVICE = "aster-seerr-broker"
PROJECT = "unified-media-shadow"
IMAGE = "sha256:e649732f3bc662d5d3f42afd00d010941011ea571d2108ed0c0a7bdf739584c1"
BASE_TAG = "unified-aster-seerr-broker:pre-low-spec-20261104"
SOURCE_SHA256 = "73be0b582b15a353cc8747f36704df9ff6cc68ca0d25723916b9fd99ff986d0a"
ROOT = Path("/mnt/Media/appdata/unified-media-shadow")
SECRETS = ROOT / "secrets"
CHECKPOINT = ROOT / "checkpoints/astertv-jen-broker-identities-20261104"
SEERR_SECRET = SECRETS / "astertv-jen-seerr-token"
ACQUISITION_SECRET = SECRETS / "astertv-jen-acquisition-token"
TAG = "unified-aster-seerr-broker:multi-token-20261104"
FALLBACK_COMPOSE = Path(
    "/mnt/Media/appdata/dockge/unified-media-shadow/.aster-checkpoints/"
    "aster-acquisition-plain-ok1/broker-candidate.yaml"
)


def run(arguments: list[str], *, timeout: int = 120) -> bytes:
    return subprocess.run(arguments, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout).stdout


def write_private(path: Path, raw: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def request(path: str, token: str, *, body: Optional[bytes] = None) -> int:
    headers = {"Authorization": "Bearer " + token,
               "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    query = urllib.request.Request("http://192.168.20.40:8788" + path,
                                   data=body, headers=headers,
                                   method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(query, timeout=15) as response:
            response.read(2 * 1024 * 1024 + 1)
            return response.status
    except urllib.error.HTTPError as error:
        error.read(65537)
        return error.code


def main() -> None:
    if os.getuid() != 0 or CHECKPOINT.exists() or SEERR_SECRET.exists() or ACQUISITION_SECRET.exists():
        raise RuntimeError("low-spec-broker-install-state")
    inspect = json.loads(run(["docker", "inspect", CONTAINER]))[0]
    labels = inspect["Config"]["Labels"]
    compose_path = Path(labels["com.docker.compose.project.config_files"])
    if not compose_path.is_file() and FALLBACK_COMPOSE.is_file():
        compose_path = FALLBACK_COMPOSE
    if (labels.get("com.docker.compose.project") != PROJECT
            or labels.get("com.docker.compose.service") != SERVICE
            or inspect["Image"] != IMAGE or not compose_path.is_file()):
        raise RuntimeError("low-spec-broker-predecessor-drift")
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    source = run(["docker", "exec", CONTAINER, "cat", "/app/aster_seerr_broker.py"])
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("low-spec-broker-source-drift")
    write_private(CHECKPOINT / "aster_seerr_broker.py.before", source)
    old = b'''    def _token(self) -> str:\n        return Path(os.environ["ASTER_SEERR_TOKEN_PATH"]).read_text(encoding="utf-8").strip()\n\n'''
    new = b'''    def _authorize_paths(self, primary: str, additional: str, error: str) -> None:\n        paths = [Path(os.environ[primary])]\n        extra = os.environ.get(additional)\n        if extra:\n            paths.append(Path(extra))\n        header = self.headers.get("Authorization", "")\n        matched = False\n        for path in paths:\n            token = path.read_text(encoding="utf-8").strip()\n            try:\n                authorize(header, token)\n            except BrokerError:\n                pass\n            else:\n                matched = True\n        if not matched:\n            raise BrokerError(error)\n\n'''
    if source.count(old) != 1:
        raise RuntimeError("low-spec-broker-token-pattern")
    candidate = source.replace(old, new)
    old = b'''    def _auth(self) -> None:\n        authorize(self.headers.get("Authorization", ""), self._token())\n\n    def _acquisition_auth(self) -> None:\n        token = Path(os.environ["ASTER_ACQUISITION_TOKEN_PATH"]).read_text(\n            encoding="utf-8").strip()\n        try:\n            authorize(self.headers.get("Authorization", ""), token)\n        except BrokerError as error:\n            if str(error) == "aster-seerr-unauthorized":\n                raise BrokerError("aster-acquisition-unauthorized") from error\n            raise\n'''
    new = b'''    def _auth(self) -> None:\n        self._authorize_paths("ASTER_SEERR_TOKEN_PATH",\n                              "ASTER_SEERR_ADDITIONAL_TOKEN_PATH",\n                              "aster-seerr-unauthorized")\n\n    def _acquisition_auth(self) -> None:\n        self._authorize_paths("ASTER_ACQUISITION_TOKEN_PATH",\n                              "ASTER_ACQUISITION_ADDITIONAL_TOKEN_PATH",\n                              "aster-acquisition-unauthorized")\n'''
    if candidate.count(old) != 1:
        raise RuntimeError("low-spec-broker-auth-pattern")
    candidate = candidate.replace(old, new)
    compile(candidate, "aster_seerr_broker.py", "exec")
    write_private(CHECKPOINT / "aster_seerr_broker.py", candidate)
    write_private(CHECKPOINT / "Dockerfile", ("FROM " + BASE_TAG + "\nCOPY --chown=root:root "
                  "aster_seerr_broker.py /app/aster_seerr_broker.py\n"
                  "RUN chmod 0644 /app/aster_seerr_broker.py\n").encode())
    original_compose = compose_path.read_bytes()
    write_private(CHECKPOINT / "compose.rollback.yaml", original_compose)
    compose = yaml.safe_load(original_compose)
    service = compose["services"][SERVICE]
    service["image"] = TAG
    service["environment"].extend([
        "ASTER_SEERR_ADDITIONAL_TOKEN_PATH=/run/unified-secrets/astertv-jen-seerr-token",
        "ASTER_ACQUISITION_ADDITIONAL_TOKEN_PATH=/run/unified-secrets/astertv-jen-acquisition-token",
    ])
    for source_path, target in (
        (SEERR_SECRET, "/run/unified-secrets/astertv-jen-seerr-token"),
        (ACQUISITION_SECRET, "/run/unified-secrets/astertv-jen-acquisition-token"),
    ):
        service["volumes"].append({"type": "bind", "source": str(source_path),
                                   "target": target, "read_only": True,
                                   "bind": {"propagation": "rprivate"}})
    candidate_compose = yaml.safe_dump(compose, sort_keys=False).encode()
    write_private(CHECKPOINT / "compose.candidate.yaml", candidate_compose)
    seerr = secrets.token_urlsafe(48)
    acquisition = secrets.token_urlsafe(48)
    write_private(SEERR_SECRET, (seerr + "\n").encode())
    write_private(ACQUISITION_SECRET, (acquisition + "\n").encode())
    try:
        run(["docker", "tag", IMAGE, BASE_TAG])
        run(["docker", "build", "-t", TAG, str(CHECKPOINT)], timeout=300)
        run(["docker", "compose", "-p", PROJECT, "-f",
             str(CHECKPOINT / "compose.candidate.yaml"), "up", "-d", "--no-deps",
             "--force-recreate", SERVICE], timeout=180)
        for _ in range(20):
            state = json.loads(run(["docker", "inspect", CONTAINER]))[0]["State"]
            if state.get("Health", {}).get("Status") == "healthy":
                break
            time.sleep(1)
        else:
            raise RuntimeError("low-spec-broker-health")
        primary_seerr = (SECRETS / "aster-seerr-tv-token").read_text().strip()
        primary_acquisition = (SECRETS / "aster-acquisition-tv-token").read_text().strip()
        if (request("/v1/discovery/media", primary_seerr) != 200
                or request("/v1/discovery/media", seerr) != 200
                or request("/v1/discovery/media", "x" * 48) != 401
                or request("/v1/acquisition", primary_acquisition, body=b"{}") != 409
                or request("/v1/acquisition", acquisition, body=b"{}") != 409
                or request("/v1/acquisition", "x" * 48, body=b"{}") != 401):
            raise RuntimeError("low-spec-broker-auth-contract")
    except Exception:
        run(["docker", "compose", "-p", PROJECT, "-f",
             str(CHECKPOINT / "compose.rollback.yaml"), "up", "-d", "--no-deps",
             "--force-recreate", SERVICE], timeout=180)
        raise
    proof = {"installed": True, "container": CONTAINER, "image": TAG,
             "primary_preserved": True, "seerr_new_status": 200,
             "acquisition_authenticated_invalid_status": 409,
             "bad_status": 401, "credential_output": False}
    write_private(CHECKPOINT / "proof.json",
                  (json.dumps(proof, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps(proof, sort_keys=True))


if __name__ == "__main__":
    main()
