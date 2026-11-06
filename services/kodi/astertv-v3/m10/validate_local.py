#!/usr/bin/env python3
"""Fail-closed repository gate for the local half of AsterTV v3 M10."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
V3 = ROOT / "services/kodi/astertv-v3"
DESIGN = ROOT / "services/kodi/astertv-design"
FLEET_TESTS = ROOT / "services/kodi/astertv-fleet/tests"
HOME_ASSISTANT_TESTS = ROOT / "services/home-assistant/aster_room_bridge"
OPERATIONS_OBSERVATION = (
    ROOT / "docs/projects/evidence/AsterTV-v3-M10-operations-observation-2026-11-05.json")
CONNECTED_ONLY = {
    "services/kodi/astertv-v3/low-spec/test_hevc_decode.py": {
        "status": "pass",
        "reason": "requires AsterTV-Jen, a transient HEVC fixture, idle player and local JSON-RPC",
        "evidence": "docs/projects/evidence/AsterTV-v3-M10-Jen-HEVC-2026-11-06.md",
    },
}
EXTERNAL_ENVIRONMENT = {
    "aster-gateway": {
        "status": "pass",
        "evidence": "docs/projects/evidence/AsterTV-v3-M10-gateway-environment-2026-11-05.md",
    },
    "live-recovery": {
        "status": "pass",
        "evidence": "docs/projects/evidence/AsterTV-v3-M10-Family-operations-and-restore-2026-11-05.md",
    },
    "operations": {
        "status": "pass",
        "evidence": "docs/projects/evidence/AsterTV-v3-M10-operations-readiness-2026-11-05.md",
    },
    "performance": {
        "status": "pass",
        "evidence": "docs/projects/evidence/AsterTV-v3-M10-Jen-HEVC-2026-11-06.md",
    },
    "walkthrough": {
        "status": "open",
        "reason": "requires non-author physical-remote acceptance",
    },
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def discover_tests() -> tuple[list[Path], list[dict]]:
    discovered = sorted(V3.rglob("test_*.py"))
    discovered += sorted(DESIGN.rglob("test_*.py"))
    discovered += sorted(FLEET_TESTS.rglob("test_*.py"))
    discovered += sorted(HOME_ASSISTANT_TESTS.glob("test_*.py"))
    runnable = []
    connected = []
    for path in discovered:
        name = relative(path)
        if name in CONNECTED_ONLY:
            connected.append({"path": name, **CONNECTED_ONLY[name]})
        else:
            runnable.append(path)
    unknown_exclusions = set(CONNECTED_ONLY) - {relative(path) for path in discovered}
    if unknown_exclusions:
        raise RuntimeError("connected-test-inventory-drift:" + ",".join(sorted(unknown_exclusions)))
    return runnable, connected


def run_tests(paths: list[Path], cache: Path) -> list[dict]:
    environment = dict(os.environ, PYTHONPYCACHEPREFIX=str(cache))
    rows = []
    for path in paths:
        completed = subprocess.run(
            [sys.executable, str(path)], cwd=ROOT, env=environment,
            text=True, capture_output=True, check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                "local-gate-failed:{}\n{}{}".format(
                    relative(path), completed.stdout, completed.stderr))
        rows.append({"path": relative(path), "outcome": "pass"})
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict:
    candidate = load("astertv_m10_candidate", V3 / "candidate/build_candidate.py")
    candidate.scan(candidate.source_files())
    if candidate.sha256_file(candidate.V2) != candidate.V2_SHA256:
        raise RuntimeError("immutable-v2-baseline-drift")

    page_audit = load("astertv_m10_page_audit", V3 / "audit_page_conformance.py")
    page_result = page_audit.audit()
    if page_result["outcome"] != "pass":
        raise RuntimeError("page-conformance-failed")

    operations = load("astertv_m10_operations", V3 / "m10/audit_operations.py")
    operations_result = operations.audit(json.loads(OPERATIONS_OBSERVATION.read_text()))
    if operations_result["outcome"] not in {"pass", "attention"}:
        raise RuntimeError("operations-audit-invalid")

    screensaver = load("astertv_m10_screensaver", V3 / "screensaver/build_candidate.py")
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        one = screensaver.build(temporary / "one.tar.gz")
        two = screensaver.build(temporary / "two.tar.gz")
        if one["sha256"] != two["sha256"] or (temporary / "one.tar.gz").read_bytes() != (temporary / "two.tar.gz").read_bytes():
            raise RuntimeError("screensaver-build-not-deterministic")
        runnable, connected = discover_tests()
        tests = run_tests(runnable, temporary / "pycache")

    return {
        "schema_version": 1,
        "outcome": "pass-with-owner-acceptance-open",
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            text=True, capture_output=True).stdout.strip(),
        "immutable_v2_sha256": candidate.V2_SHA256,
        "secret_scan_files": len(candidate.source_files()),
        "page_conformance": {
            "pages": page_result["page_count"],
            "focus_controls": sum(row["focus_controls"] for row in page_result["pages"]),
            "failures": page_result["failure_count"],
        },
        "screensaver_candidate_sha256": one["sha256"],
        "operations_readiness": operations_result,
        "local_test_files": len(tests),
        "tests": tests,
        "connected_tests": connected,
        "external_environment_gates": EXTERNAL_ENVIRONMENT,
    }


def main() -> int:
    print(json.dumps(validate(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
