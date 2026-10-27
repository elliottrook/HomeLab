#!/usr/bin/env python3
"""Validate the source-only SA3 proposal-gateway release packet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("sa3-proposal-gateway-manifest.json")
EXPECTED_RUNTIME = {
    "target": "LXC104",
    "service": "aster-agent.service",
    "restart_required": True,
    "model_restart": False,
    "model_change": False,
    "automatic_routing": False,
    "observation_authority": False,
    "repair_authority": False,
}
EXPECTED_TARGETS = {
    "/opt/aster-agent/aster_agent.py",
    "/opt/aster-agent/sysadmin_proposal_boundary.py",
    "/opt/aster-agent/sysadmin_proposal_transport.py",
    "/opt/aster-agent/sysadmin_proposal_gateway.py",
}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(), object_pairs_hook=_unique_object)
    if set(manifest) != {
        "schema_version", "release_id", "source_commit", "candidate_review", "files", "runtime"
    } or manifest["schema_version"] != 1:
        raise ValueError("invalid release manifest shape")
    if manifest["release_id"] != "sa3-candidate-e-journal-gateway-20261027":
        raise ValueError("unexpected release identity")
    source_commit = manifest["source_commit"]
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise ValueError("invalid source commit")
    review = manifest["candidate_review"]
    if review != {
        "candidate_source_commit": "73901010",
        "packet_freeze_commit": "8d1cfb2a",
        "independent_review": "passed",
        "receipt": "services/aster-agent/evals/sa3-candidate-e-independent-review-receipt.json",
        "receipt_sha256": "09b19ca26a254279625f541dfa72e2b92b788083c520a1283964ee9f5765a9c6",
    }:
        raise ValueError("candidate review boundary changed")
    if _digest(root / review["receipt"]) != review["receipt_sha256"]:
        raise ValueError("independent review receipt hash mismatch")
    if manifest["runtime"] != EXPECTED_RUNTIME:
        raise ValueError("runtime authority boundary changed")
    files = manifest["files"]
    if not isinstance(files, list) or len(files) != 4:
        raise ValueError("unexpected release file count")
    targets: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {
            "source", "target", "sha256", "predecessor_sha256"
        }:
            raise ValueError("invalid release file entry")
        source = item["source"]
        target = item["target"]
        if not isinstance(source, str) or not source.startswith("services/aster-agent/"):
            raise ValueError("invalid release source")
        if not isinstance(target, str) or target in targets:
            raise ValueError("invalid or duplicate release target")
        targets.add(target)
        if _digest(root / source) != item["sha256"]:
            raise ValueError("release source hash mismatch")
        predecessor = item["predecessor_sha256"]
        if predecessor is not None and (not isinstance(predecessor, str) or len(predecessor) != 64):
            raise ValueError("invalid predecessor hash")
    if targets != EXPECTED_TARGETS:
        raise ValueError("release target set changed")
    return {
        "release_id": manifest["release_id"],
        "files": len(files),
        "independent_review": review["independent_review"],
        "automatic_routing": False,
        "repair_authority": False,
        "manifest_sha256": _digest(manifest_path),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
