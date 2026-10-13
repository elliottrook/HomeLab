"""Validate a sealed fictional assistant-answer holdout without printing cases.

The candidate runner must receive cases.jsonl only. This validator is for the
custodian and prints structural counts and SHA-256 digests, never case text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


CASE_FIELDS = {"id", "class", "fictional_user_request", "frozen_clock",
               "synthetic_source_records", "private_context_locality_constraint",
               "permitted_capability_set", "maximum_tool_scope"}
KEY_FIELDS = {"id", "correct_outcome_category", "expected_observable_behavior",
              "rubric_checks", "prohibited_claims"}


def _load(path: Path) -> tuple[list[dict], str]:
    raw = path.read_bytes()
    lines = raw.splitlines()
    if not lines or any(not line for line in lines):
        raise ValueError(f"{path.name}: empty record")
    rows = [json.loads(line) for line in lines]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path.name}: record must be an object")
    return rows, hashlib.sha256(raw).hexdigest()


def validate(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("holdout directory must be a real directory")
    if root.stat().st_mode & 0o077:
        raise ValueError("holdout directory must be owner-only")
    files = [root / name for name in ("cases.jsonl", "answer-key.jsonl", "manifest.json")]
    if any(path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077
           for path in files):
        raise ValueError("holdout files must be regular owner-only files")
    cases, case_hash = _load(files[0])
    keys, key_hash = _load(files[1])
    manifest_raw = files[2].read_bytes()
    manifest = json.loads(manifest_raw)
    required = {"schema_version", "case_count", "family_counts", "outcome_counts",
                "private_context_locality_case_count", "files"}
    if not isinstance(manifest, dict) or not required <= set(manifest):
        raise ValueError("manifest schema mismatch")
    if not isinstance(manifest["files"], dict):
        raise ValueError("manifest file hashes must be keyed by filename")
    if any(set(row) != CASE_FIELDS for row in cases):
        raise ValueError("case schema mismatch")
    if any(set(row) != KEY_FIELDS for row in keys):
        raise ValueError("answer-key schema mismatch")
    case_ids = [row["id"] for row in cases]
    key_ids = [row["id"] for row in keys]
    if any(not isinstance(i, str) or not i for i in case_ids + key_ids):
        raise ValueError("invalid ID")
    if len(case_ids) != len(set(case_ids)) or len(key_ids) != len(set(key_ids)):
        raise ValueError("duplicate ID")
    if case_ids != key_ids:
        raise ValueError("case and key order/IDs differ")
    counts = dict(Counter(row["class"] for row in cases))
    outcomes = dict(Counter(row["correct_outcome_category"] for row in keys))
    locality_count = sum(bool(row["private_context_locality_constraint"]) for row in cases)
    if manifest["case_count"] != len(cases) or manifest["family_counts"] != counts:
        raise ValueError("manifest case count mismatch")
    if manifest["outcome_counts"] != outcomes or manifest["private_context_locality_case_count"] != locality_count:
        raise ValueError("manifest label/locality count mismatch")
    pinned = manifest["files"]
    for name, digest in (("cases.jsonl", case_hash), ("answer-key.jsonl", key_hash)):
        if name not in pinned:
            raise ValueError(f"manifest missing digest: {name}")
        value = pinned[name]
        expected = value.get("sha256") if isinstance(value, dict) else value
        if expected != digest:
            raise ValueError(f"manifest digest mismatch: {name}")
    return {"case_count": len(cases), "family_counts": counts,
            "outcome_counts": outcomes, "private_context_locality_case_count": locality_count,
            "cases_sha256": case_hash, "answer_key_sha256": key_hash,
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "schema_version": manifest["schema_version"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.directory), sort_keys=True))


if __name__ == "__main__":
    main()
