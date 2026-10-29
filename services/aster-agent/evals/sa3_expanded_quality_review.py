"""Verify exact files and an independent SA3 expanded-quality review receipt."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


RECEIPT_FIELDS = frozenset({
    "schema_version", "review_id", "reviewer", "independent", "reviewed_commit",
    "manifest_sha256", "decision", "findings", "limitations",
})


def _bytes_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def load_json(path: Path):
    return json.loads(path.read_text(), object_pairs_hook=_unique_object)


def verify_manifest(root: Path, manifest_path: Path) -> dict:
    manifest = load_json(manifest_path)
    expected = {
        "schema_version", "review_id", "reviewed_commit", "material_files",
        "canonical_packet_sha256", "canonical_keys_sha256", "required_findings",
        "review_only", "model_calls_authorized", "tool_calls_authorized",
        "routing_authorized", "repair_authorized",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected or manifest["schema_version"] != 1:
        raise ValueError("invalid review manifest")
    if (manifest["review_only"] is not True
            or any(manifest[name] is not False for name in (
                "model_calls_authorized", "tool_calls_authorized",
                "routing_authorized", "repair_authorized"))):
        raise ValueError("unsafe review manifest")
    files = manifest["material_files"]
    if not isinstance(files, dict) or not files:
        raise ValueError("empty review manifest")
    for relative, expected_hash in files.items():
        path = root / relative
        if not path.is_file() or path.is_symlink() or _bytes_sha256(path) != expected_hash:
            raise ValueError("review material mismatch")
    findings = manifest["required_findings"]
    if (not isinstance(findings, list) or len(findings) != len(set(findings))
            or any(not isinstance(item, str) or not item for item in findings)):
        raise ValueError("invalid required findings")
    return manifest


def verify_receipt(root: Path, manifest_path: Path, receipt_path: Path) -> dict:
    manifest = verify_manifest(root, manifest_path)
    receipt = load_json(receipt_path)
    if not isinstance(receipt, dict) or frozenset(receipt) != RECEIPT_FIELDS:
        raise ValueError("invalid review receipt")
    if (receipt["schema_version"] != 1
            or receipt["review_id"] != manifest["review_id"]
            or receipt["reviewed_commit"] != manifest["reviewed_commit"]
            or receipt["manifest_sha256"] != _bytes_sha256(manifest_path)
            or receipt["independent"] is not True
            or not isinstance(receipt["reviewer"], str) or not receipt["reviewer"].strip()
            or not isinstance(receipt["limitations"], str)):
        raise ValueError("review receipt binding mismatch")
    findings = receipt["findings"]
    required = manifest["required_findings"]
    if (not isinstance(findings, dict) or set(findings) != set(required)
            or any(type(value) is not bool for value in findings.values())):
        raise ValueError("invalid review findings")
    decision = receipt["decision"]
    if decision not in {"pass", "reject"}:
        raise ValueError("invalid review decision")
    accepted = decision == "pass" and all(findings.values())
    if decision == "pass" and not accepted:
        raise ValueError("contradictory pass receipt")
    return {
        "schema": "aster-sa3-expanded-quality-review-receipt.v1",
        "review_id": manifest["review_id"],
        "reviewed_commit": manifest["reviewed_commit"],
        "decision": decision,
        "accepted": accepted,
        "reviewer": receipt["reviewer"],
    }
