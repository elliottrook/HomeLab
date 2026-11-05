#!/usr/local/bin/python3
"""Allow only local discovery ahead of the Family TCL Internet block."""
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
    "/conf/backup/config-astertv-m7-family-tcl-discovery-before-20261105.xml"
)
PROOF = Path(
    "/conf/backup/config-astertv-m7-family-tcl-discovery-proof-20261105.json"
)
EXPECTED = "b58ea04f7866997ef40ddf395299578fb509eb6c0239fdf0fcad005fe0e4dd80"
BLOCK_ID = "bfaf8ab8-9e66-43fe-8be0-f25a6ca13d47"
SOURCE = "192.168.30.162"
RULES = (
    {
        "uuid": "47e080ff-acde-466a-becb-0b364bb3e120",
        "sequence": "925",
        "destination_net": "224.0.0.251",
        "destination_port": "5353",
        "description": "AsterTV M7 allow Family TCL local mDNS discovery",
    },
    {
        "uuid": "30b56966-e872-497d-a947-bf9a90bbb012",
        "sequence": "926",
        "destination_net": "239.255.255.250",
        "destination_port": "1900",
        "description": "AsterTV M7 allow Family TCL local SSDP discovery",
    },
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-m7-tcl-discovery-", dir=path.parent)
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
    block = next((rule for rule in rules if rule.get("uuid") == BLOCK_ID), None)
    if (
        block is None
        or block.findtext("sequence") != "950"
        or block.findtext("action") != "block"
        or block.findtext("source_net") != SOURCE
        or block.findtext("destination_net") != "any"
    ):
        raise RuntimeError("block-rule-drift")
    if any(
        rule.get("uuid") in {item["uuid"] for item in RULES}
        or rule.findtext("sequence") in {item["sequence"] for item in RULES}
        for rule in rules
    ):
        raise RuntimeError("discovery-rule-collision")

    parent = next(parent for parent in root.iter() if block in list(parent))
    index = list(parent).index(block)
    for offset, values in enumerate(RULES):
        candidate = copy.deepcopy(block)
        candidate.set("uuid", values["uuid"])
        fields = {
            "enabled": "1",
            "sequence": values["sequence"],
            "action": "pass",
            "interface": "opt2",
            "direction": "in",
            "ipprotocol": "inet",
            "protocol": "UDP",
            "source_net": SOURCE,
            "source_not": "0",
            "destination_net": values["destination_net"],
            "destination_not": "0",
            "destination_port": values["destination_port"],
            "description": values["description"],
        }
        for key, value in fields.items():
            element = candidate.find(key)
            if element is None:
                element = ET.SubElement(candidate, key)
            element.text = value
        parent.insert(index + offset, candidate)

    descriptor = os.open(
        str(CHECKPOINT), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    after = ET.tostring(root, encoding="utf-8")
    atomic(CONFIG, after, CONFIG.stat().st_mode & 0o777)
    installed = {
        rule.get("uuid"): rule
        for rule in ET.parse(CONFIG).getroot().iter("rule")
        if rule.get("uuid") in {item["uuid"] for item in RULES}
    }
    if len(installed) != 2 or any(
        installed[item["uuid"]].findtext("destination_net") != item["destination_net"]
        or installed[item["uuid"]].findtext("destination_port") != item["destination_port"]
        or installed[item["uuid"]].findtext("action") != "pass"
        for item in RULES
    ):
        raise RuntimeError("post-write-verification")
    result = {
        "installed": True,
        "source": SOURCE,
        "allows": [
            f'{item["destination_net"]}:{item["destination_port"]}/UDP' for item in RULES
        ],
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
        raise SystemExit("usage: allow_family_tcl_discovery.py apply|rollback")
    apply() if sys.argv[1] == "apply" else rollback()
