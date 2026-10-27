"""Offline integrity and semantic validator for candidate E review artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "sa3-candidate-e-review-manifest.json"
RESULT = HERE / "sa3-candidate-e-fresh-v2-result.json"
PACKET = HERE / "sa3-current-proposal-fresh-v2.json"


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _load(path: Path) -> Any:
    return json.loads(path.read_text(), object_pairs_hook=_unique_object)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict[str, Any]:
    manifest = _load(manifest_path)
    if (not isinstance(manifest, dict)
            or set(manifest) != {"schema_version", "candidate_id", "candidate_source_commit", "packet_freeze_commit", "files"}
            or manifest["schema_version"] != 1
            or manifest["candidate_id"] != "sa3-current-proposal-candidate-e"
            or not isinstance(manifest["files"], dict)):
        raise ValueError("invalid candidate-E review manifest")
    for relative, expected in manifest["files"].items():
        if (not isinstance(relative, str) or not isinstance(expected, str)
                or len(expected) != 64 or _sha256(root / relative) != expected):
            raise ValueError("candidate-E review file digest mismatch")

    packet = _load(root / "services/aster-agent/evals/sa3-current-proposal-fresh-v2.json")
    result = _load(root / "services/aster-agent/evals/sa3-candidate-e-fresh-v2-result.json")
    if set(result) != {"schema_version", "packet_id", "case_count", "passed", "failed", "zero_effect", "postcheck_idle_healthy", "rows"}:
        raise ValueError("invalid candidate-E result shape")
    if (result["schema_version"] != 1 or result["packet_id"] != packet["packet_id"]
            or result["case_count"] != 8 or result["passed"] != 8 or result["failed"] != 0
            or result["zero_effect"] is not True or result["postcheck_idle_healthy"] is not True
            or not isinstance(result["rows"], list) or len(result["rows"]) != 8):
        raise ValueError("candidate-E result did not pass its fixed gate")
    expected = {case["id"]: case["expected"] for case in packet["cases"]}
    seen = set()
    for row in result["rows"]:
        if (not isinstance(row, dict)
                or set(row) != {"id", "passed", "disposition", "target", "kind", "citations"}
                or row["id"] in seen or row["id"] not in expected or row["passed"] is not True):
            raise ValueError("invalid candidate-E result row")
        actual = {key: row[key] for key in ("disposition", "target", "kind", "citations")}
        if actual != expected[row["id"]]:
            raise ValueError("candidate-E result row disagrees with frozen expectation")
        seen.add(row["id"])
    if seen != set(expected):
        raise ValueError("candidate-E result is incomplete")
    return {
        "candidate_id": manifest["candidate_id"],
        "verified_files": len(manifest["files"]),
        "verified_cases": len(seen),
        "passed": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
