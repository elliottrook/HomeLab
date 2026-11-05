"""Install the bounded candidate-j file/semantic digest contract correction."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess

from sa3_candidate_j_exclusion_correction_install import (
    EPUB_PINS, MANIFEST, REMOTE, UNIT_PREFIX, WRAPPER, _quiet,
)
from sa3_evidence_envelope_inactive_install import (
    GUEST_ROOT, HOST_ROOT, InstallError, atomic, digest, regular, source,
)


TRANSACTION = "sa3_candidate_j_evidence_matrix_transaction.py"
CHECKPOINT = Path(
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-j-digest-r2-20261105")
GUEST_CHECKPOINT = str(CHECKPOINT)
OLD = {
    WRAPPER: "a883c144ead962dc5862c54005a90157db173e88667122a89a23496796f05f2a",
    TRANSACTION: "a7a1ccc86308a6dc8991dbc666be464b0a7eb9746862c5842f829bcaa7be35ab",
    MANIFEST: "1f048141e77cffd3684c6ab50199f83bac7cb170356441756e8fb0b9ab74c845",
}
NEW = {
    WRAPPER: "fc283224e86319ebcc267be481f6a9cf4c9b27801bb822b0b3b0ad19d5c506f4",
    TRANSACTION: "c2fbcf6b81a934c5d043648142acb019c4b571d9ed2c3373a5c59b7438994108",
    MANIFEST: "99e41a1e7e3e92a3a5860ada3877c7cfadf207cccc9a56b641477b918c1d9fda",
}


def _guest(op: str, data: bytes | None = None) -> None:
    value = {"path": GUEST_ROOT + "/" + WRAPPER,
             "checkpoint": GUEST_CHECKPOINT, "name": WRAPPER,
             "old": OLD[WRAPPER], "new": NEW[WRAPPER]}
    if data is not None:
        value["data"] = base64.b64encode(data).decode()
    result = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/python3",
                             "-B", "-c", REMOTE, op), input=json.dumps(value),
                            capture_output=True, text=True, timeout=30,
                            check=False)
    if result.returncode:
        raise InstallError("GUEST_" + op.upper() + ":"
                           + (result.stderr or result.stdout).strip()[-160:])


def _derived_manifest(installed: bytes) -> bytes:
    value = json.loads(installed.decode("utf-8"))
    pins = value.get("pins") if isinstance(value, dict) else None
    if (value.get("schema") != "aster-lab-hours-release-manifest.v1"
            or value.get("release") != "sa3-candidate-j-runner-source-v14"
            or not isinstance(pins, dict) or len(pins) != 41
            or pins.get(WRAPPER) != OLD[WRAPPER]
            or pins.get(TRANSACTION) != OLD[TRANSACTION]
            or any(pins.get(name) != expected
                   for name, expected in EPUB_PINS.items())):
        raise InstallError("INSTALLED_MANIFEST_SHAPE_INVALID")
    pins[WRAPPER] = NEW[WRAPPER]
    pins[TRANSACTION] = NEW[TRANSACTION]
    result = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    if digest(result) != NEW[MANIFEST]:
        raise InstallError("DERIVED_MANIFEST_HASH_INVALID")
    return result


def install(stage: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise InstallError("ROOT_REQUIRED")
    if CHECKPOINT.exists():
        raise InstallError("CHECKPOINT_EXISTS")
    for suffix in (".service", ".timer"):
        if Path("/etc/systemd/system", UNIT_PREFIX + suffix).exists():
            raise InstallError("UNIT_PRESENT:" + suffix)
    _quiet()
    current = {}
    for name, expected in OLD.items():
        current[name] = regular(HOST_ROOT / name, 0o644)
        if digest(current[name]) != expected:
            raise InstallError("BASELINE_DRIFT:" + name)
    replacement = {
        WRAPPER: source(stage, "scripts/local-ai/" + WRAPPER, NEW[WRAPPER]),
        TRANSACTION: source(
            stage, "scripts/local-ai/" + TRANSACTION, NEW[TRANSACTION]),
        MANIFEST: _derived_manifest(current[MANIFEST]),
    }
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name, data in current.items():
        atomic(CHECKPOINT / name, data, 0o600)
        if digest(regular(CHECKPOINT / name, 0o600)) != OLD[name]:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    _guest("preflight")
    guest_started = False
    try:
        for name in (WRAPPER, TRANSACTION, MANIFEST):
            atomic(HOST_ROOT / name, replacement[name], 0o644)
        guest_started = True
        _guest("install", replacement[WRAPPER])
        _guest("verify")
        for name, expected in NEW.items():
            if digest(regular(HOST_ROOT / name, 0o644)) != expected:
                raise InstallError("POSTCHECK:" + name)
        proof = (
            "import aster_llama_sa3_candidate_j_evidence_matrix_wrapper as w;"
            "import sa3_candidate_j_evidence_matrix_transaction as t;"
            "assert w.FIXTURE_FILE_SHA256!=w.FIXTURE_SEMANTIC_SHA256;"
            "assert t.FIXTURE_FILE_SHA256!=t.FIXTURE_SEMANTIC_SHA256;"
            "assert w.FIXTURE_SEMANTIC_SHA256==t.FIXTURE_SEMANTIC_SHA256")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": str(HOST_ROOT)}
        host = subprocess.run(("/usr/bin/python3", "-B", "-c", proof),
                              env=env, capture_output=True, text=True,
                              timeout=30, check=False)
        if host.returncode:
            raise InstallError("HOST_PROOF:" + host.stderr[-160:])
        guest = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + GUEST_ROOT,
            "/usr/bin/python3", "-B", "-c",
            "import aster_llama_sa3_candidate_j_evidence_matrix_wrapper as w;"
            "assert w.FIXTURE_FILE_SHA256!=w.FIXTURE_SEMANTIC_SHA256"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest.returncode:
            raise InstallError("GUEST_PROOF:" + guest.stderr[-160:])
        _quiet()
        return {"state": "installed-inactive", "host_replaced": 3,
                "guest_replaced": 1, "checkpoint": "retained",
                "service_restart": False, "workload_effect": "not-attempted",
                "booking": "absent"}
    except BaseException:
        if guest_started:
            _guest("rollback")
        for name in reversed((WRAPPER, TRANSACTION, MANIFEST)):
            target = HOST_ROOT / name
            if digest(regular(target, 0o644)) != NEW[name]:
                raise InstallError("ROLLBACK_UNCERTAIN:" + name)
            atomic(target, regular(CHECKPOINT / name, 0o600), 0o644)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"},
                         sort_keys=True))
        return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True))
        return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
