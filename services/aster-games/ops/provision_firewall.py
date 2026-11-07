#!/usr/local/bin/python3
"""Install two least-privilege NPM-to-Aster-Games OPNsense rules."""

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
CHECKPOINT = Path("/conf/backup/config-aster-games-before-20261106.xml")
PROOF = Path("/conf/backup/config-aster-games-proof-20261106.json")
EXPECTED = "5cb0ca6b05780b56b731020df5b7e71dd0340cd03230d8ff49f9636d021d97a2"
TEMPLATE_ID = "7ced83a2-f0e3-4dcb-a84f-8ae2e666c26b"
RULES = (
    ("eb348fc0-4d6f-49bb-a883-cd17d19c3c55", "8080", "Allow NPM to Aster Games RomM"),
    ("3af0a87d-3fed-4bf0-80b5-d24cca701f42", "6868", "Allow NPM to Aster Games ROMarr"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-games-firewall-", dir=path.parent)
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
    root = ET.fromstring(before)
    existing = {item.get("uuid"): item for item in root.iter("rule")}
    if all(rule_id in existing for rule_id, _, _ in RULES):
        valid = all(
            existing[rule_id].findtext("source_net") == "192.168.50.23"
            and existing[rule_id].findtext("destination_net") == "192.168.20.38"
            and existing[rule_id].findtext("destination_port") == port
            and existing[rule_id].findtext("action") == "pass"
            for rule_id, port, _ in RULES
        )
        if not valid:
            raise RuntimeError("existing-rule-drift")
        print(json.dumps({"installed": True, "outcome": "already-present"}))
        return
    if sha(before) != EXPECTED or CHECKPOINT.exists() or PROOF.exists():
        raise RuntimeError("predecessor-or-checkpoint-guard")
    template = existing.get(TEMPLATE_ID)
    if (
        template is None
        or template.findtext("interface") != "opt4"
        or template.findtext("source_net") != "192.168.50.23"
        or template.findtext("action") != "pass"
        or template.findtext("protocol") != "TCP"
    ):
        raise RuntimeError("template-rule-drift")
    parent = next(parent for parent in root.iter() if template in list(parent))
    index = list(parent).index(template) + 1
    for offset, (rule_id, port, description) in enumerate(RULES):
        candidate = copy.deepcopy(template)
        candidate.set("uuid", rule_id)
        fields = {
            "sequence": "2194",
            "destination_net": "192.168.20.38",
            "destination_port": port,
            "description": description,
        }
        for key, value in fields.items():
            candidate.find(key).text = value
        parent.insert(index + offset, candidate)
    descriptor = os.open(CHECKPOINT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    after = ET.tostring(root, encoding="utf-8")
    atomic(CONFIG, after, CONFIG.stat().st_mode & 0o777)
    proof = {
        "installed": True,
        "source": "192.168.50.23",
        "destination": "192.168.20.38",
        "ports": [8080, 6868],
        "before_sha256": EXPECTED,
        "after_sha256": sha(after),
        "checkpoint": str(CHECKPOINT),
    }
    atomic(PROOF, json.dumps(proof, sort_keys=True).encode(), 0o600)
    print(json.dumps(proof, sort_keys=True))


def rollback() -> None:
    proof = json.loads(PROOF.read_text())
    if sha(CONFIG.read_bytes()) != proof["after_sha256"]:
        raise RuntimeError("rollback-current-drift")
    before = CHECKPOINT.read_bytes()
    if sha(before) != EXPECTED:
        raise RuntimeError("rollback-checkpoint-drift")
    atomic(CONFIG, before, CONFIG.stat().st_mode & 0o777)
    print(json.dumps({"rolled_back": True, "reload_required": True}))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"apply", "rollback"}:
        raise SystemExit("usage: provision_firewall.py apply|rollback")
    apply() if sys.argv[1] == "apply" else rollback()
