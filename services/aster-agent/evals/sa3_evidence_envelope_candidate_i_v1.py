"""Validate candidate-i's source freeze and untouched-evaluation boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


FILES = {
    "sa3-evidence-envelope-candidate-i-quality-v1.json":
        "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0",
    "sa3-evidence-envelope-development-v1.json":
        "733a6a6fc664ccf2b29dc1ab61affce9bfb04eb07b6a937946ccdb379988d1cd",
    "sa3_deterministic_evidence_envelope_v1.py":
        "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3",
    "sa3_deterministic_evidence_envelope_v2.py":
        "4ca154c6ea0b0738adc3c9e21544ac0a6d3c05473852f88f97b6e5e7e1611943",
    "sa3_evidence_envelope_batch_v2.py":
        "eaeddb10d5a36df5dd3f3646691d19857f094f2872086d7b78056d6ff7c70d4e",
    "sa3_evidence_envelope_runner_v2.py":
        "58b932a65afb6d88d4624d3d74b0d4d021091e0989c74e1ca4cf0afdede9188c",
}
CONTROLS = {
    "checks": "deterministic-visible-usable-observations-only",
    "diagnosis": "bounded-model-or-deterministic-fallback",
    "effects": "always-empty",
    "outcome": "deterministic-plan-or-clarify",
    "verification": "deterministic-registered-sources-only",
}
EVALUATION = {
    "case_count": 20, "minimum_abstentions": 6, "reviewers": 3,
    "required_passes": 18, "all_abstentions_required": True,
    "no_false_completion_failures": 0, "untouched_packet_required": True,
}
FORBIDDEN = {
    "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a",
    "d8c7945924a98bfae45522fd4ac9f377871db3243136b4a00617263cf44e9066",
}


def validate(manifest: object, source_dir: Path) -> dict[str, object]:
    if not isinstance(manifest, dict) or set(manifest) != {
            "schema", "candidate_alias", "status", "files", "controls",
            "evaluation", "forbidden_evaluation_sha256", "tools", "authority",
            "automatic_routing", "model_calls_authorized", "repair_authorized",
            "model_promotion_authorized"}:
        raise ValueError("candidate-i manifest fields differ")
    if (manifest["schema"] != "aster-sa3-evidence-envelope-candidate.v2"
            or manifest["candidate_alias"] != "candidate-i"
            or manifest["status"] != "source-frozen-not-run"
            or manifest["files"] != FILES
            or manifest["controls"] != CONTROLS
            or manifest["evaluation"] != EVALUATION
            or set(manifest["forbidden_evaluation_sha256"]) != FORBIDDEN
            or manifest["tools"] != "none"
            or manifest["authority"] != "none"
            or manifest["automatic_routing"] != "off"
            or manifest["model_calls_authorized"] is not False
            or manifest["repair_authorized"] is not False
            or manifest["model_promotion_authorized"] is not False):
        raise ValueError("candidate-i manifest value differs")
    for name, expected in FILES.items():
        path = source_dir / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("candidate-i source missing:" + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("candidate-i source changed:" + name)
    return {
        "schema": manifest["schema"], "candidate_alias": "candidate-i",
        "file_count": len(FILES), "source_frozen": True,
        "untouched_evaluation_required": True, "authority": "none",
        "automatic_routing": "off", "model_calls_authorized": False,
    }


def load(path: Path) -> dict[str, object]:
    return validate(json.loads(path.read_text(encoding="utf-8")), path.parent)
