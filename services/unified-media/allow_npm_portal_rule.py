"""Add the exact NPM-to-portal OPNsense path; dry-run unless --apply."""

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
SOURCE_UUID = "3a1ee37e-0288-4b85-8a0e-9323f43b563a"
RULE_UUID = "c2d6e7f8-9012-4abc-8def-3456789abc01"
SEQUENCE = "3200"
raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))
assert not any(rule.get("uuid") == RULE_UUID for rule in rules), "rule already exists"
assert not any(rule.findtext("sequence") == SEQUENCE for rule in rules), "sequence already in use"
source = next(rule for rule in rules if rule.get("uuid") == SOURCE_UUID)
expected = {
    "interface": "opt4", "source_net": "192.168.50.23",
    "destination_net": "192.168.20.40", "destination_port": "8096",
    "protocol": "TCP", "action": "pass", "enabled": "1", "quick": "1",
}
assert all(source.findtext(key) == value for key, value in expected.items()), "reference rule drift"
match = re.search(r'<rule uuid="' + re.escape(SOURCE_UUID) + r'">.*?</rule>', raw, re.S)
assert match, "reference rule XML missing"
candidate = match.group().replace(SOURCE_UUID, RULE_UUID)
candidate = candidate.replace("<sequence>2192</sequence>", f"<sequence>{SEQUENCE}</sequence>")
candidate = candidate.replace("<destination_port>8096</destination_port>", "<destination_port>8787</destination_port>")
candidate = re.sub(
    r"<description>.*?</description>",
    "<description>NPM to Unified Media Recommendations portal</description>",
    candidate,
    flags=re.S,
)
new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
assert len(list(parsed.iter("rule"))) == len(rules) + 1
print({"rule_uuid": RULE_UUID, "source": "192.168.50.23",
       "destination": "192.168.20.40:8787/TCP", "interface": "opt4",
       "mode": "apply" if "--apply" in sys.argv else "dry-run"})
if "--apply" in sys.argv:
    backup = Path("/conf/backup") / (
        "config-unified-media-npm-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml"
    )
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.unified-media-npm-candidate")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
