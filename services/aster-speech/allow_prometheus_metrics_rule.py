"""Add the exact Prometheus-to-Aster metrics path on OPNsense.

Run on OPNsense. Dry-run is the default. ``--apply`` creates a protected
configuration backup and writes the candidate; reload the filter separately.
"""

from __future__ import annotations

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
SOURCE_UUID = "5468fe48-c98c-4ce6-ac1f-eeb118583fcb"
RULE_UUID = "f4355d1a-94f2-49ee-a6cf-da15159354bf"
SEQUENCE = "1976"

raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))
assert not any(rule.get("uuid") == RULE_UUID for rule in rules), "rule already exists"
assert not any(rule.findtext("sequence") == SEQUENCE for rule in rules), "sequence already in use"
source = next(rule for rule in rules if rule.get("uuid") == SOURCE_UUID)
expected = {
    "interface": "opt3",
    "source_net": "192.168.20.11",
    "destination_net": "192.168.70.14",
    "destination_port": "10300",
    "protocol": "TCP",
    "action": "pass",
    "enabled": "1",
    "quick": "1",
}
assert all(source.findtext(key) == value for key, value in expected.items()), "reference rule drift"

match = re.search(r'<rule uuid="' + re.escape(SOURCE_UUID) + r'">.*?</rule>', raw, re.S)
assert match, "reference rule XML missing"
candidate = match.group().replace(SOURCE_UUID, RULE_UUID)
for old, new_value in {
    "<sequence>1975</sequence>": f"<sequence>{SEQUENCE}</sequence>",
    "<source_net>192.168.20.11</source_net>": "<source_net>192.168.20.31</source_net>",
    "<destination_port>10300</destination_port>": "<destination_port>9131</destination_port>",
}.items():
    assert candidate.count(old) == 1, f"reference field drift: {old}"
    candidate = candidate.replace(old, new_value)
candidate = re.sub(
    r"<description>.*?</description>",
    "<description>Allow Prometheus to Aster Voice metrics</description>",
    candidate,
    count=1,
    flags=re.S,
)

new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
new_rules = list(parsed.iter("rule"))
assert len(new_rules) == len(rules) + 1
created = next(rule for rule in new_rules if rule.get("uuid") == RULE_UUID)
assert created.findtext("source_net") == "192.168.20.31"
assert created.findtext("destination_net") == "192.168.70.14"
assert created.findtext("destination_port") == "9131"

print({
    "rule_uuid": RULE_UUID,
    "source": "192.168.20.31",
    "destination": "192.168.70.14:9131/TCP",
    "interface": "opt3",
    "sequence": SEQUENCE,
    "mode": "apply" if "--apply" in sys.argv else "dry-run",
})

if "--apply" in sys.argv:
    backup = Path("/conf/backup") / (
        "config-aster-metrics-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml"
    )
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.aster-metrics-candidate")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
