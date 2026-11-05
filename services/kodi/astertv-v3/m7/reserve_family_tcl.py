#!/usr/local/bin/python3
"""Reserve the Family TCL address that its exact privacy rule protects."""
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
    "/conf/backup/config-astertv-m7-family-tcl-reservation-before-20261105.xml"
)
PROOF = Path(
    "/conf/backup/config-astertv-m7-family-tcl-reservation-proof-20261105.json"
)
EXPECTED = "c81417953c6c764be0279bb36234d368682c7fba800d9a5d3278df1bd866236b"
REFERENCE = "ebc4a8d7-aaa4-42e3-8245-090600d0d6a2"
HOST_ID = "bf6b7e34-99a2-4bce-928d-ed042a9fcf84"
HOSTNAME = "family-room-tv"
ADDRESS = "192.168.30.162"
MAC = "0c:91:60:75:7c:5c"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-m7-tcl-dhcp-", dir=path.parent)
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
    dnsmasq = root.find("dnsmasq")
    if dnsmasq is None:
        raise RuntimeError("dnsmasq-missing")
    hosts = list(dnsmasq.findall("hosts"))
    if any(host.get("uuid") == HOST_ID for host in hosts):
        raise RuntimeError("reservation-already-present")
    if any(
        host.findtext("ip") == ADDRESS
        or (host.findtext("hwaddr") or "").lower() == MAC
        or host.findtext("host") == HOSTNAME
        for host in hosts
    ):
        raise RuntimeError("reservation-identity-collision")
    reference = next((host for host in hosts if host.get("uuid") == REFERENCE), None)
    if (
        reference is None
        or reference.findtext("ip") != "192.168.30.164"
        or (reference.findtext("hwaddr") or "").lower() != "00:17:88:22:42:e5"
    ):
        raise RuntimeError("reference-reservation-drift")

    candidate = copy.deepcopy(reference)
    candidate.set("uuid", HOST_ID)
    values = {
        "host": HOSTNAME,
        "domain": "",
        "local": "0",
        "ip": ADDRESS,
        "client_id": "",
        "hwaddr": MAC,
        "lease_time": "",
        "ignore": "0",
        "set_tag": "",
        "descr": "Family Room TCL TV",
        "comments": "AsterTV M7 local-only television",
    }
    for key, value in values.items():
        element = candidate.find(key)
        if element is None:
            element = ET.SubElement(candidate, key)
        element.text = value
    dnsmasq.insert(list(dnsmasq).index(reference) + 1, candidate)

    descriptor = os.open(
        str(CHECKPOINT), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    after = ET.tostring(root, encoding="utf-8")
    atomic(CONFIG, after, CONFIG.stat().st_mode & 0o777)
    installed = [host for host in ET.parse(CONFIG).getroot().findall("dnsmasq/hosts") if host.get("uuid") == HOST_ID]
    if (
        len(installed) != 1
        or installed[0].findtext("ip") != ADDRESS
        or (installed[0].findtext("hwaddr") or "").lower() != MAC
    ):
        raise RuntimeError("post-write-verification")
    result = {
        "installed": True,
        "host_id": HOST_ID,
        "hostname": HOSTNAME,
        "address": ADDRESS,
        "mac": MAC,
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
        raise SystemExit("usage: reserve_family_tcl.py apply|rollback")
    apply() if sys.argv[1] == "apply" else rollback()
