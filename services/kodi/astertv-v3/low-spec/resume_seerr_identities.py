#!/usr/bin/env python3
"""Resume the checked AsterTV-Jen broker rollout after Docker health delay."""

import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request


ROOT = Path("/mnt/Media/appdata/unified-media-shadow")
CHECKPOINT = ROOT / "checkpoints/astertv-jen-broker-identities-20261104"
SECRETS = ROOT / "secrets"
SEERR = SECRETS / "astertv-jen-seerr-token"
ACQUISITION = SECRETS / "astertv-jen-acquisition-token"
CANDIDATE = CHECKPOINT / "compose.candidate.yaml"
ROLLBACK = CHECKPOINT / "compose.rollback.yaml"
PROOF = CHECKPOINT / "proof.json"
PROJECT = "unified-media-shadow"
SERVICE = "aster-seerr-broker"
CONTAINER = "unified-aster-seerr-broker"
TAG = "unified-aster-seerr-broker:multi-token-20261104"


def run(arguments, timeout=180):
    return subprocess.run(arguments, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout).stdout


def status(path, token, body=None):
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    query = urllib.request.Request("http://192.168.20.40:8788" + path,
        data=body, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(query, timeout=15) as response:
            response.read(2 * 1024 * 1024 + 1)
            return response.status
    except urllib.error.HTTPError as error:
        error.read(65537)
        return error.code


def main():
    if (os.getuid() != 0 or PROOF.exists()
            or not all(path.is_file() for path in (SEERR, ACQUISITION, CANDIDATE, ROLLBACK))):
        raise RuntimeError("low-spec-broker-resume-state")
    if TAG.encode() not in CANDIDATE.read_bytes():
        raise RuntimeError("low-spec-broker-resume-candidate")
    for path in (SEERR, ACQUISITION):
        value = path.read_text().strip()
        if not 32 <= len(value) <= 512 or any(c.isspace() for c in value):
            raise RuntimeError("low-spec-broker-resume-secret")
        os.chown(path, 65534, 65534)
        os.chmod(path, 0o600)
    try:
        run(["docker", "compose", "-p", PROJECT, "-f", str(CANDIDATE),
             "up", "-d", "--no-deps", "--force-recreate", SERVICE])
        for _ in range(45):
            try:
                if urllib.request.urlopen("http://192.168.20.40:8788/health",
                                          timeout=2).status == 200:
                    break
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(1)
        else:
            raise RuntimeError("low-spec-broker-resume-health")
        primary_seerr = (SECRETS / "aster-seerr-tv-token").read_text().strip()
        primary_acquisition = (SECRETS / "aster-acquisition-tv-token").read_text().strip()
        checks = {
            "primary_seerr": status("/v1/discovery/media", primary_seerr),
            "new_seerr": status("/v1/discovery/media", SEERR.read_text().strip()),
            "bad_seerr": status("/v1/discovery/media", "x" * 48),
            "primary_acquisition": status("/v1/acquisition", primary_acquisition, b"{}"),
            "new_acquisition": status("/v1/acquisition", ACQUISITION.read_text().strip(), b"{}"),
            "bad_acquisition": status("/v1/acquisition", "x" * 48, b"{}"),
        }
        if checks != {"primary_seerr": 200, "new_seerr": 200, "bad_seerr": 401,
                      "primary_acquisition": 409, "new_acquisition": 409,
                      "bad_acquisition": 401}:
            raise RuntimeError("low-spec-broker-resume-contract")
    except Exception:
        run(["docker", "compose", "-p", PROJECT, "-f", str(ROLLBACK),
             "up", "-d", "--no-deps", "--force-recreate", SERVICE])
        raise
    proof = {"installed": True, "image": TAG, "primary_preserved": True,
             "seerr_new_status": 200, "acquisition_authenticated_invalid_status": 409,
             "bad_status": 401, "credential_output": False}
    descriptor = os.open(PROOF, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(proof, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(proof, sort_keys=True))


if __name__ == "__main__":
    main()
