#!/usr/local/bin/python3
"""Add or roll back the exact Family TCL Internet-deny rule."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET


CONFIG = Path("/conf/config.xml")
CHECKPOINT = Path(
    "/conf/backup/config-astertv-m7-family-tcl-wan-before-20261105.xml"
)
PROOF = Path(
    "/conf/backup/config-astertv-m7-family-tcl-wan-proof-20261105.json"
)
EXPECTED = "3ccad73e4dff26c5fe0365133c74836c5917089582e5d996ef4d49ae33dca3eb"
REFERENCE = "dd2386fe-4bc3-4656-95dd-f784cb4f825a"
RULE_ID = "bfaf8ab8-9e66-43fe-8be0-f25a6ca13d47"
VALUES = {
    "enabled": "1",
    "sequence": "950",
    "action": "block",
    "interface": "opt2",
    "direction": "in",
    "ipprotocol": "inet",
    "protocol": "any",
    "source_net": "192.168.30.162",
    "source_not": "0",
    "destination_net": "any",
    "destination_not": "0",
    "description": "AsterTV M7 block Family TCL Internet egress",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-m7-tcl-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply() -> None:
    before = CONFIG.read_bytes()
    if sha(before) != EXPECTED or CHECKPOINT.exists() or PROOF.exists():
        raise RuntimeError("predecessor-or-checkpoint-guard")
    root = ET.fromstring(before)
    rules = list(root.iter("rule"))
    if any(rule.get("uuid") == RULE_ID for rule in rules):
        raise RuntimeError("rule-already-present")
    if any(rule.findtext("sequence") == VALUES["sequence"] for rule in rules):
        raise RuntimeError("sequence-already-used")
    reference = next((rule for rule in rules if rule.get("uuid") == REFERENCE), None)
    expected_reference = {
        "sequence": "1000",
        "action": "pass",
        "interface": "opt2",
        "source_net": "opt2",
        "destination_net": "any",
    }
    if reference is None or any(
        reference.findtext(key) != value for key, value in expected_reference.items()
    ):
        raise RuntimeError("reference-rule-drift")

    candidate = copy.deepcopy(reference)
    candidate.set("uuid", RULE_ID)
    for key, value in VALUES.items():
        element = candidate.find(key)
        if element is None:
            element = ET.SubElement(candidate, key)
        element.text = value
    for key in ("destination_port", "log"):
        element = candidate.find(key)
        if element is not None:
            candidate.remove(element)

    parent = next(parent for parent in root.iter() if reference in list(parent))
    parent.insert(list(parent).index(reference), candidate)
    descriptor = os.open(
        str(CHECKPOINT), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())

    after = ET.tostring(root, encoding="utf-8")
    atomic(CONFIG, after, CONFIG.stat().st_mode & 0o777)
    installed = [rule for rule in ET.parse(CONFIG).getroot().iter("rule") if rule.get("uuid") == RULE_ID]
    if len(installed) != 1 or any(
        installed[0].findtext(key) != value for key, value in VALUES.items()
    ):
        raise RuntimeError("post-write-verification")
    result = {
        "installed": True,
        "rule_id": RULE_ID,
        "source": VALUES["source_net"],
        "action": "block",
        "before_sha256": EXPECTED,
        "after_sha256": sha(after),
        "checkpoint": str(CHECKPOINT),
        "reload_required": True,
    }
    atomic(PROOF, json.dumps(result, sort_keys=True).encode(), 0o600)
    print(json.dumps(result, sort_keys=True))


def rollback() -> None:
    proof = json.loads(PROOF.read_text())
    if sha(CONFIG.read_bytes()) != proof["after_sha256"]:
        raise RuntimeError("rollback-current-drift")
    before = CHECKPOINT.read_bytes()
    if sha(before) != EXPECTED:
        raise RuntimeError("rollback-checkpoint-drift")
    atomic(CONFIG, before, CONFIG.stat().st_mode & 0o777)
    print(json.dumps({"rolled_back": True, "reload_required": True}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"apply", "rollback"}:
        raise SystemExit("usage: apply_family_tcl_wan_block.py apply|rollback")
    apply() if sys.argv[1] == "apply" else rollback()
