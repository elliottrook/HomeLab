#!/usr/local/bin/python3
"""Add only HA-to-AsterTVProd TCP/22 beside the existing lab-feed rule."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET


CONFIG = Path("/conf/config.xml")
EXPECTED = "15c7cc111a52dc725ccb31109dca2b1aaf63fa7f71f63103e087a5516561f60f"
REFERENCE = "d0584fb0-b226-52a6-9fc9-e9983fcb48d4"
RULE_ID = "e5f0fcb0-3ff0-5bd8-a44b-e810fe7a1687"
CHECKPOINT = Path("/conf/backup/config-aster-home-feed-prod-before-20261030.xml")
VALUES = {
    "enabled": "1",
    "sequence": "1851",
    "action": "pass",
    "interface": "opt3",
    "direction": "in",
    "ipprotocol": "inet",
    "protocol": "TCP",
    "source_net": "192.168.20.11",
    "source_not": "0",
    "destination_net": "192.168.1.157",
    "destination_not": "0",
    "destination_port": "22",
    "description": "Aster Home HA to AsterTVProd restricted display feed",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    before = CONFIG.read_bytes()
    if sha(before) != EXPECTED or CHECKPOINT.exists():
        raise RuntimeError("firewall predecessor/checkpoint guard")
    root = ET.fromstring(before)
    rules = list(root.iter("rule"))
    if any(rule.get("uuid") == RULE_ID for rule in rules):
        raise RuntimeError("production feed rule already exists")
    if any(rule.findtext("sequence") == VALUES["sequence"] for rule in rules):
        raise RuntimeError("production feed sequence already used")
    reference = next((rule for rule in rules if rule.get("uuid") == REFERENCE), None)
    if reference is None:
        raise RuntimeError("lab feed reference missing")
    for key, value in {
        "interface": "opt3",
        "source_net": "192.168.20.11",
        "destination_net": "192.168.1.140",
        "destination_port": "22",
    }.items():
        if reference.findtext(key) != value:
            raise RuntimeError("lab feed reference drift: " + key)

    candidate = copy.deepcopy(reference)
    candidate.set("uuid", RULE_ID)
    for key, value in VALUES.items():
        node = candidate.find(key)
        if node is None:
            node = ET.SubElement(candidate, key)
        node.text = value
    parent = next(node for node in root.iter() if reference in list(node))
    parent.append(candidate)

    checkpoint_fd = os.open(str(CHECKPOINT), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(checkpoint_fd, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    if CHECKPOINT.read_bytes() != before:
        raise RuntimeError("firewall checkpoint mismatch")
    with tempfile.TemporaryDirectory(prefix="aster-home-prod-restore-", dir="/root") as folder:
        restored = Path(folder) / "config.xml"
        restored.write_bytes(CHECKPOINT.read_bytes())
        ET.parse(restored)
        if sha(restored.read_bytes()) != EXPECTED:
            raise RuntimeError("firewall isolated restore mismatch")

    metadata = CONFIG.stat()
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-home-prod-", dir=CONFIG.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(ET.tostring(root, encoding="utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, metadata.st_mode & 0o777)
        os.chown(temporary, metadata.st_uid, metadata.st_gid)
        if CONFIG.read_bytes() != before:
            raise RuntimeError("firewall concurrent change")
        os.replace(temporary, CONFIG)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    verify = ET.parse(CONFIG).getroot()
    installed = [rule for rule in verify.iter("rule") if rule.get("uuid") == RULE_ID]
    if len(installed) != 1 or any(installed[0].findtext(key) != value for key, value in VALUES.items()):
        raise RuntimeError("firewall post-write verification")
    print(json.dumps({
        "installed": True,
        "rule_id": RULE_ID,
        "source": "192.168.20.11",
        "destination": "192.168.1.157",
        "tcp_port": 22,
        "checkpoint": str(CHECKPOINT),
        "isolated_restore": True,
        "reload_required": True,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
