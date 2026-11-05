#!/usr/local/bin/python3
"""Extend the exact M7 Onkyo permit from TCP to TCP/UDP, with rollback."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

CONFIG = Path("/conf/config.xml")
CHECKPOINT = Path("/conf/backup/config-astertv-m7-onkyo-before-udp-20261105.xml")
PROOF = Path("/conf/backup/config-astertv-m7-onkyo-udp-proof-20261105.json")
EXPECTED = "de67739d3c0774ed5e28bf30e3f3e6063bea5ae2d6426d31a30c7a2acf1f2a58"
RULE_ID = "af4ef3e0-e9ad-45c7-b2a7-2fe59cb50cff"
EXPECTED_FIELDS = {
    "sequence": "1852", "action": "pass", "interface": "opt3", "direction": "in",
    "source_net": "192.168.20.11", "destination_net": "192.168.1.186",
    "destination_port": "60128", "protocol": "TCP",
    "description": "AsterTV M7 HA to Family Onkyo native control",
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic(path: Path, data: bytes, mode: int) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".astertv-m7-udp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, mode); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def apply() -> None:
    before = CONFIG.read_bytes()
    if sha(before) != EXPECTED or CHECKPOINT.exists() or PROOF.exists():
        raise RuntimeError("predecessor-or-checkpoint-guard")
    root = ET.fromstring(before)
    matches = [r for r in root.iter("rule") if r.get("uuid") == RULE_ID]
    if len(matches) != 1 or any(matches[0].findtext(k) != v for k, v in EXPECTED_FIELDS.items()):
        raise RuntimeError("tcp-rule-drift")
    fd = os.open(str(CHECKPOINT), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(before); stream.flush(); os.fsync(stream.fileno())
    matches[0].find("protocol").text = "TCP/UDP"
    after = ET.tostring(root, encoding="utf-8")
    atomic(CONFIG, after, CONFIG.stat().st_mode & 0o777)
    installed = [r for r in ET.parse(CONFIG).getroot().iter("rule") if r.get("uuid") == RULE_ID]
    if len(installed) != 1 or installed[0].findtext("protocol") != "TCP/UDP":
        raise RuntimeError("post-write-verification")
    result = {"expanded": True, "protocol": "TCP/UDP", "source": "192.168.20.11",
              "destination": "192.168.1.186", "port": 60128,
              "before_sha256": EXPECTED, "after_sha256": sha(after),
              "checkpoint": str(CHECKPOINT), "reload_required": True}
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
        raise SystemExit("usage: expand_onkyo_firewall_udp.py apply|rollback")
    apply() if sys.argv[1] == "apply" else rollback()
