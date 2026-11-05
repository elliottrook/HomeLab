"""Offline integrity and semantic validator for candidate E review artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "sa3-candidate-e-review-manifest.json"
RESULT = HERE / "sa3-candidate-e-fresh-v2-result.json"
PACKET = HERE / "sa3-current-proposal-fresh-v2.json"
SOURCE_FILES = frozenset({
    "services/aster-agent/sysadmin_proposal_boundary.py",
    "services/aster-agent/sysadmin_proposal_transport.py",
})
PACKET_FILE = "services/aster-agent/evals/sa3-current-proposal-fresh-v2.json"
RESULT_FILE = "services/aster-agent/evals/sa3-candidate-e-fresh-v2-result.json"
FILES = SOURCE_FILES | {PACKET_FILE, RESULT_FILE}
COMMIT_RE = re.compile(r"[0-9a-f]{8,40}")


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _load(path: Path) -> Any:
    return json.loads(path.read_text(), object_pairs_hook=_unique_object)


def _decode(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)


def _git_blob(commit: str, relative: str) -> bytes:
    if COMMIT_RE.fullmatch(commit) is None or relative not in FILES:
        raise ValueError("candidate-E review commit or path is invalid")
    result = subprocess.run(("git", "show", f"{commit}:{relative}"), cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise ValueError("candidate-E historical review blob is unavailable")
    return result.stdout


def validate(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict[str, Any]:
    manifest = _load(manifest_path)
    if (not isinstance(manifest, dict)
            or set(manifest) != {"schema_version", "candidate_id",
                                 "candidate_source_commit", "packet_freeze_commit",
                                 "review_package_commit", "files"}
            or manifest["schema_version"] != 1
            or manifest["candidate_id"] != "sa3-current-proposal-candidate-e"
            or manifest["candidate_source_commit"] != "73901010"
            or manifest["packet_freeze_commit"] != "8d1cfb2a"
            or manifest["review_package_commit"] != "7d3d3508"
            or not isinstance(manifest["files"], dict)
            or set(manifest["files"]) != FILES):
        raise ValueError("invalid candidate-E review manifest")
    contents = {}
    for relative, expected in manifest["files"].items():
        if root == ROOT:
            commit = (manifest["candidate_source_commit"] if relative in SOURCE_FILES
                      else manifest["packet_freeze_commit"] if relative == PACKET_FILE
                      else manifest["review_package_commit"])
            data = _git_blob(commit, relative)
        else:
            data = (root / relative).read_bytes()
        if (not isinstance(expected, str) or len(expected) != 64
                or hashlib.sha256(data).hexdigest() != expected):
            raise ValueError("candidate-E review file digest mismatch")
        contents[relative] = data

    packet = _decode(contents[PACKET_FILE])
    result = _decode(contents[RESULT_FILE])
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
