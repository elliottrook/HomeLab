#!/usr/local/bin/python3
"""Correct the Family TCL reservation from its Bluetooth to DHCP MAC."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET


CONFIG = Path("/conf/config.xml")
CHECKPOINT = Path(
    "/conf/backup/config-astertv-m7-family-tcl-mac-correction-before-20261105.xml"
)
PROOF = Path(
    "/conf/backup/config-astertv-m7-family-tcl-mac-correction-proof-20261105.json"
)
EXPECTED = "839df4b89ce747d963a59d52d8527b9ffcca4ee5a69440fd11ff55db5e0de60d"
HOST_ID = "bf6b7e34-99a2-4bce-928d-ed042a9fcf84"
ADDRESS = "192.168.30.162"
OLD_MAC = "0c:91:60:75:7c:5d"
NEW_MAC = "0c:91:60:75:7c:5c"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-m7-tcl-mac-", dir=path.parent)
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
    matches = [
        host for host in root.findall("dnsmasq/hosts") if host.get("uuid") == HOST_ID
    ]
    if (
        len(matches) != 1
        or matches[0].findtext("ip") != ADDRESS
        or (matches[0].findtext("hwaddr") or "").lower() != OLD_MAC
    ):
        raise RuntimeError("reservation-drift")
    if any(
        (host.findtext("hwaddr") or "").lower() == NEW_MAC and host is not matches[0]
        for host in root.findall("dnsmasq/hosts")
    ):
        raise RuntimeError("correct-mac-collision")

    descriptor = os.open(
        str(CHECKPOINT), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    matches[0].find("hwaddr").text = NEW_MAC
    after = ET.tostring(root, encoding="utf-8")
    atomic(CONFIG, after, CONFIG.stat().st_mode & 0o777)
    installed = [
        host for host in ET.parse(CONFIG).getroot().findall("dnsmasq/hosts")
        if host.get("uuid") == HOST_ID
    ]
    if len(installed) != 1 or installed[0].findtext("hwaddr") != NEW_MAC:
        raise RuntimeError("post-write-verification")
    result = {
        "corrected": True,
        "host_id": HOST_ID,
        "address": ADDRESS,
        "old_mac": OLD_MAC,
        "new_mac": NEW_MAC,
        "before_sha256": EXPECTED,
        "after_sha256": sha(after),
        "checkpoint": str(CHECKPOINT),
        "dnsmasq_reload_required": True,
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
    print(json.dumps({"rolled_back": True, "dnsmasq_reload_required": True}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"apply", "rollback"}:
        raise SystemExit("usage: correct_family_tcl_reservation_mac.py apply|rollback")
    apply() if sys.argv[1] == "apply" else rollback()
