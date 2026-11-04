"""Validate the exact source-frozen D4 candidate-g manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


FILES = {
    "sa3-evidence-envelope-development-v1.json": "733a6a6fc664ccf2b29dc1ab61affce9bfb04eb07b6a937946ccdb379988d1cd",
    "sa3_deterministic_evidence_envelope_v1.py": "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3",
    "sa3_evidence_envelope_runner_v1.py": "372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352",
}
CONTROLS = {
    "checks": "deterministic-visible-usable-observations-only",
    "effects": "always-empty",
    "model_role": "diagnosis-and-verification-prose-only",
    "outcome": "deterministic-plan-or-clarify",
    "secret_request": "deterministic-clarify-no-model-call",
    "unsafe_prose": "deterministic-fallback",
}


def _load_unique(raw: bytes):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate candidate manifest key")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def validate(manifest_raw: bytes, source_dir: Path) -> dict[str, object]:
    value = _load_unique(manifest_raw)
    if not isinstance(value, dict) or set(value) != {
        "schema", "candidate_alias", "status", "files", "controls", "tools",
        "authority", "automatic_routing", "model_calls_authorized",
        "repair_authorized", "model_promotion_authorized",
    }:
        raise ValueError("candidate-g manifest fields differ")
    if (value["schema"] != "aster-sa3-evidence-envelope-candidate.v1"
            or value["candidate_alias"] != "candidate-g"
            or value["status"] != "source-frozen-not-run"
            or value["files"] != FILES
            or value["controls"] != CONTROLS
            or value["tools"] != "none"
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"
            or value["model_calls_authorized"] is not False
            or value["repair_authorized"] is not False
            or value["model_promotion_authorized"] is not False):
        raise ValueError("candidate-g manifest value differs")
    for name, expected_sha256 in FILES.items():
        path = source_dir / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"candidate-g source missing: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
            raise ValueError(f"candidate-g source changed: {name}")
    return {
        "schema": value["schema"],
        "candidate_alias": value["candidate_alias"],
        "file_count": len(FILES),
        "source_frozen": True,
        "model_calls_authorized": False,
        "automatic_routing": "off",
        "authority": "none",
    }
