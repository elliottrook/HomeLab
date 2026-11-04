#!/usr/bin/env python3
"""Add the three narrow OPNsense paths needed by AsterTV-Jen.

Run on OPNsense. The default is a validating dry-run; ``--apply`` takes a
protected configuration checkpoint and writes the candidate. Filter reload is
deliberately separate so the written XML can be inspected first.
"""

from __future__ import annotations

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
TARGET = "192.168.1.180"
SPECS = (
    {
        "source_uuid": "feb35a23-036b-494a-9d37-a61509de25ff",
        "uuid": "0ed352aa-f14f-4b92-a05d-94e58ca5eb80",
        "sequence": "3088",
        "source": TARGET,
        "destination": "192.168.50.23",
        "port": "443",
        "description": "AsterTV-Jen HTTPS to private app gateway for Books",
    },
    {
        "source_uuid": "8c3d6b4e-2c4b-4d1d-9d4c-6d1e3af0a271",
        "uuid": "8cb0da40-9b94-4b02-8167-2895b8881e30",
        "sequence": "3089",
        "source": TARGET,
        "destination": "192.168.20.40",
        "port": "8788",
        "description": "AsterTV-Jen Seerr catalogue broker",
    },
    {
        "source_uuid": "e5f0fcb0-3ff0-5bd8-a44b-e810fe7a1687",
        "uuid": "0191e92d-f255-4392-998d-faa0412066ed",
        "sequence": "1849",
        "source": "192.168.20.11",
        "destination": TARGET,
        "port": "22",
        "description": "Home Assistant display feed to AsterTV-Jen",
    },
)


def rule_xml(raw: str, rule_uuid: str) -> tuple[re.Match[str], str]:
    match = re.search(
        r'<rule uuid="' + re.escape(rule_uuid) + r'">.*?</rule>', raw, re.S
    )
    assert match, "reference rule XML missing: " + rule_uuid
    return match, match.group()


raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))
existing_uuids = {rule.get("uuid") for rule in rules}
existing_sequences = {rule.findtext("sequence") for rule in rules}
for spec in SPECS:
    assert spec["uuid"] not in existing_uuids, "rule already exists: " + spec["uuid"]
    assert spec["sequence"] not in existing_sequences, "sequence in use: " + spec["sequence"]

new = raw
for spec in SPECS:
    parsed = ElementTree.fromstring(new)
    source = next(rule for rule in parsed.iter("rule")
                  if rule.get("uuid") == spec["source_uuid"])
    expected = {
        "protocol": "TCP", "action": "pass", "enabled": "1", "quick": "1"
    }
    assert all(source.findtext(key) == value for key, value in expected.items()), (
        "reference rule drift: " + spec["source_uuid"]
    )
    match, candidate = rule_xml(new, spec["source_uuid"])
    candidate = candidate.replace(spec["source_uuid"], spec["uuid"], 1)
    for element, value in (
        ("sequence", spec["sequence"]),
        ("source_net", spec["source"]),
        ("destination_net", spec["destination"]),
        ("destination_port", spec["port"]),
        ("description", spec["description"]),
    ):
        candidate, count = re.subn(
            rf"<{element}>.*?</{element}>",
            f"<{element}>{value}</{element}>", candidate, count=1, flags=re.S,
        )
        assert count == 1, "reference field missing: " + element
    new = new[:match.end()] + "\n          " + candidate + new[match.end():]

parsed = ElementTree.fromstring(new)
new_rules = list(parsed.iter("rule"))
assert len(new_rules) == len(rules) + len(SPECS)
for spec in SPECS:
    created = next(rule for rule in new_rules if rule.get("uuid") == spec["uuid"])
    assert created.findtext("sequence") == spec["sequence"]
    assert created.findtext("source_net") == spec["source"]
    assert created.findtext("destination_net") == spec["destination"]
    assert created.findtext("destination_port") == spec["port"]

print({"mode": "apply" if "--apply" in sys.argv else "dry-run",
       "target": TARGET, "rules": len(SPECS), "credential_output": False})

if "--apply" in sys.argv:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = Path("/conf/backup") / f"config-astertv-jen-access-before-{stamp}.xml"
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.astertv-jen-access-candidate")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
