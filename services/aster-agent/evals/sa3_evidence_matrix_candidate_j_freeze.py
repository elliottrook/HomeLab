"""Fail-closed source freeze for candidate-j public development."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name(
    "sa3-evidence-matrix-candidate-j-source-freeze-v1.json")
FILES = frozenset({
    "services/aster-agent/evals/sa3_evidence_matrix_candidate_j_contract.py",
    "services/aster-agent/evals/sa3_evidence_matrix_candidate_j_runner.py",
    "services/aster-agent/evals/sa3_evidence_matrix_candidate_j_public.py",
    "services/aster-agent/evals/sa3_evidence_matrix_candidate_j_batch.py",
    "services/aster-agent/evals/sa3-evidence-matrix-candidate-j-public-v1.json",
})


def validate(root: Path = ROOT, manifest: Path = MANIFEST) -> dict[str, object]:
    value = json.loads(manifest.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or set(value) != {
            "schema", "candidate_alias", "files", "spent_quality_packets",
            "model_calls_authorized", "authority", "automatic_routing"}
            or value["schema"] != "aster-sa3-evidence-matrix-source-freeze.v1"
            or value["candidate_alias"] != "candidate-j"
            or set(value["files"]) != FILES
            or value["spent_quality_packets"] != {
                "candidate-g": "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a",
                "candidate-i": "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0"}
            or value["model_calls_authorized"] is not False
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"):
        raise ValueError("candidate-j source freeze is invalid")
    for relative, expected in value["files"].items():
        path = root / relative
        if (not path.is_file() or path.is_symlink()
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
            raise ValueError("candidate-j frozen source differs")
    return {
        "schema": value["schema"], "candidate_alias": "candidate-j",
        "file_count": len(FILES), "model_calls_authorized": False,
        "authority": "none", "automatic_routing": "off",
    }
