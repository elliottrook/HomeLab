#!/usr/local/bin/python3
"""Add or roll back the exact HA-to-Family-Onkyo control permit."""
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
CHECKPOINT = Path("/conf/backup/config-astertv-m7-onkyo-before-20261105.xml")
PROOF = Path("/conf/backup/config-astertv-m7-onkyo-proof-20261105.json")
EXPECTED = "773b14f0df38582da8ee6d37cc9874201af5f43100af192ecd587cfc2f8b119f"
REFERENCE = "e5f0fcb0-3ff0-5bd8-a44b-e810fe7a1687"
RULE_ID = "af4ef3e0-e9ad-45c7-b2a7-2fe59cb50cff"
VALUES = {
    "enabled": "1",
    "sequence": "1852",
    "action": "pass",
    "interface": "opt3",
    "direction": "in",
    "ipprotocol": "inet",
    "protocol": "TCP",
    "source_net": "192.168.20.11",
    "source_not": "0",
    "destination_net": "192.168.1.186",
    "destination_not": "0",
    "destination_port": "60128",
    "description": "AsterTV M7 HA to Family Onkyo native control",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-m7-", dir=path.parent)
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
    if reference is None:
        raise RuntimeError("reference-rule-missing")
    expected_reference = {
        "interface": "opt3",
        "source_net": "192.168.20.11",
        "destination_net": "192.168.1.157",
        "destination_port": "22",
    }
    if any(reference.findtext(key) != value for key, value in expected_reference.items()):
        raise RuntimeError("reference-rule-drift")

    candidate = copy.deepcopy(reference)
    candidate.set("uuid", RULE_ID)
    for key, value in VALUES.items():
        node = candidate.find(key)
        if node is None:
            node = ET.SubElement(candidate, key)
        node.text = value
    parent = next(node for node in root.iter() if reference in list(node))
    parent.append(candidate)

    checkpoint_fd = os.open(
        str(CHECKPOINT), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(checkpoint_fd, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    ET.parse(CHECKPOINT)
    if sha(CHECKPOINT.read_bytes()) != EXPECTED:
        raise RuntimeError("checkpoint-mismatch")

    after = ET.tostring(root, encoding="utf-8")
    metadata = CONFIG.stat()
    atomic(CONFIG, after, metadata.st_mode & 0o777)
    installed = [rule for rule in ET.parse(CONFIG).getroot().iter("rule") if rule.get("uuid") == RULE_ID]
    if len(installed) != 1 or any(installed[0].findtext(key) != value for key, value in VALUES.items()):
        raise RuntimeError("post-write-verification")
    result = {
        "installed": True,
        "rule_id": RULE_ID,
        "source": VALUES["source_net"],
        "destination": VALUES["destination_net"],
        "tcp_port": int(VALUES["destination_port"]),
        "checkpoint": str(CHECKPOINT),
        "before_sha256": EXPECTED,
        "after_sha256": sha(after),
        "reload_required": True,
    }
    atomic(PROOF, json.dumps(result, sort_keys=True).encode(), 0o600)
    print(json.dumps(result, sort_keys=True))


def rollback() -> None:
    proof = json.loads(PROOF.read_text())
    current = CONFIG.read_bytes()
    if sha(current) != proof["after_sha256"]:
        raise RuntimeError("rollback-current-drift")
    checkpoint = CHECKPOINT.read_bytes()
    if sha(checkpoint) != proof["before_sha256"] or proof["before_sha256"] != EXPECTED:
        raise RuntimeError("rollback-checkpoint-drift")
    ET.fromstring(checkpoint)
    metadata = CONFIG.stat()
    atomic(CONFIG, checkpoint, metadata.st_mode & 0o777)
    if sha(CONFIG.read_bytes()) != EXPECTED:
        raise RuntimeError("rollback-verification")
    print(json.dumps({"rolled_back": True, "reload_required": True}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"apply", "rollback"}:
        raise SystemExit("usage: apply_onkyo_firewall.py apply|rollback")
    apply() if sys.argv[1] == "apply" else rollback()
