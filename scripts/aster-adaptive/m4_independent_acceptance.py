"""Validate, but never create, the human-controlled M4 acceptance record."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re


SCHEMA = "aster-m4-independent-acceptance.v1"
ARTIFACT_SHA256 = "9a3e0447adbf27f24bf5d9ab777ebbd5565bbce7873f554034304a4ce88fea38"
LEDGER_HEAD = "sha256:59fa02fe1a196ba123c447d4e773bd9404290970f4446113c8dd61b1b12cc7c9"
DECISIONS = {"retain", "reject", "request-more-evidence"}
CUSTODY = {"human-controlled-offline-record", "independently-controlled-device",
           "independently-controlled-account"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def validate(path: Path) -> dict[str, object]:
    value = json.loads(path.read_bytes(), object_pairs_hook=_unique)
    required = {"schema", "reviewer", "decision", "accepted_commit",
                "artifact_sha256", "ledger_head", "custody_method",
                "custody_reference_sha256", "reviewed_at", "data_scope",
                "private_collection_authorized", "authority", "limits"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("acceptance fields differ")
    if (value["schema"] != SCHEMA or value["decision"] not in DECISIONS
            or value["artifact_sha256"] != ARTIFACT_SHA256
            or value["ledger_head"] != LEDGER_HEAD
            or value["custody_method"] not in CUSTODY
            or not HEX40.fullmatch(value["accepted_commit"])
            or not HEX64.fullmatch(value["custody_reference_sha256"])
            or value["data_scope"] != "synthetic-only"
            or value["private_collection_authorized"] is not False
            or value["authority"] != "not-granted"):
        raise ValueError("acceptance identity or boundary differs")
    if not isinstance(value["reviewer"], str) or not value["reviewer"].strip():
        raise ValueError("reviewer is missing")
    try:
        reviewed = datetime.fromisoformat(value["reviewed_at"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError("review time is invalid") from error
    if reviewed.tzinfo is None or reviewed.utcoffset() != timezone.utc.utcoffset(reviewed):
        raise ValueError("review time must be UTC")
    limits = value["limits"]
    if (not isinstance(limits, list) or not limits
            or any(not isinstance(item, str) or not item.strip() for item in limits)):
        raise ValueError("review limits are required")
    return {"schema":"aster-m4-independent-acceptance-validation.v1",
            "status":"valid", "decision":value["decision"],
            "accepted_commit":value["accepted_commit"],
            "artifact_sha256":ARTIFACT_SHA256,"ledger_head":LEDGER_HEAD,
            "data_scope":"synthetic-only","authority":"not-granted"}


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record",type=Path)
    args=parser.parse_args()
    print(json.dumps(validate(args.record),sort_keys=True,separators=(",",":")))
