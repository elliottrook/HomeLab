"""Add the narrowly scoped OPNsense path for the TrueNAS shadow refresher.

Run on OPNsense. Dry-run is the default; ``--apply`` creates a protected
config backup, inserts one host-to-host TCP rule, and leaves reload to the
operator so the candidate can be inspected first.
"""

from __future__ import annotations

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
SOURCE_UUID = "f07d5aab-f429-49b6-8715-46c3aa829fd0"
RULE_UUID = "b4f1e1b3-6b3a-4d8b-b3c2-7a1e9c4d5201"
SEQUENCE = "1974"

raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))
assert not any(rule.get("uuid") == RULE_UUID for rule in rules), "rule already exists"
assert not any(rule.findtext("sequence") == SEQUENCE for rule in rules), "sequence already in use"
source = next(rule for rule in rules if rule.get("uuid") == SOURCE_UUID)
expected = {
    "interface": "opt3",
    "source_net": "192.168.20.40",
    "destination_net": "192.168.50.25",
    "destination_port": "3493",
    "protocol": "TCP",
    "action": "pass",
    "enabled": "1",
    "quick": "1",
}
assert all(source.findtext(key) == value for key, value in expected.items()), "reference rule drift"

match = re.search(r'<rule uuid="' + re.escape(SOURCE_UUID) + r'">.*?</rule>', raw, re.S)
assert match, "reference rule XML missing"
candidate = match.group().replace(SOURCE_UUID, RULE_UUID)
candidate = candidate.replace("<sequence>1971</sequence>", f"<sequence>{SEQUENCE}</sequence>")
candidate = candidate.replace("<destination_net>192.168.50.25</destination_net>",
                              "<destination_net>192.168.70.12</destination_net>")
candidate = candidate.replace("<destination_port>3493</destination_port>",
                              "<destination_port>11435</destination_port>")
candidate = re.sub(
    r"<description>.*?</description>",
    "<description>Allow TrueNAS unified media shadow to Aster explanations</description>",
    candidate,
    flags=re.S,
)
new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
assert len(list(parsed.iter("rule"))) == len(rules) + 1

print({
    "rule_uuid": RULE_UUID,
    "source": "192.168.20.40",
    "destination": "192.168.70.12:11435/TCP",
    "interface": "opt3",
    "mode": "apply" if "--apply" in sys.argv else "dry-run",
})

if "--apply" in sys.argv:
    backup = Path("/conf/backup") / (
        "config-unified-media-aster-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml"
    )
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.unified-media-candidate")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
