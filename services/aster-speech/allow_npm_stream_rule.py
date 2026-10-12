"""Add the exact NPM-to-Aster canonical streaming path on OPNsense.

Run on OPNsense. Dry-run is the default. ``--apply`` creates a protected
configuration backup and writes the candidate; reload the filter separately.
"""

from __future__ import annotations

import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
RULE_UUID = "c69d946a-f769-4cdf-8bb8-29aa34ae4529"

raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))

def matches(rule: ElementTree.Element, port: str) -> bool:
    expected = {
        "source_net": "192.168.50.23",
        "destination_net": "192.168.70.14",
        "destination_port": port,
        "protocol": "TCP",
        "action": "pass",
        "enabled": "1",
        "quick": "1",
    }
    return all(rule.findtext(key) == value for key, value in expected.items())

current = [rule for rule in rules if rule.get("uuid") == RULE_UUID]
if current:
    assert len(current) == 1 and matches(current[0], "9131"), "existing rule drift"
    print({"rule_uuid": RULE_UUID, "status": "already-present", "mode": "apply" if "--apply" in sys.argv else "dry-run"})
    raise SystemExit(0)

sources = [rule for rule in rules if matches(rule, "9130")]
assert len(sources) == 1, "expected exactly one NPM-to-legacy-speech reference rule"
source = sources[0]
source_uuid = source.get("uuid")
assert source_uuid and uuid.UUID(source_uuid), "invalid reference UUID"
match = re.search(r'<rule uuid="' + re.escape(source_uuid) + r'">.*?</rule>', raw, re.S)
assert match, "reference rule XML missing"
candidate = match.group().replace(source_uuid, RULE_UUID, 1)
assert candidate.count("<destination_port>9130</destination_port>") == 1
candidate = candidate.replace("<destination_port>9130</destination_port>", "<destination_port>9131</destination_port>")
candidate = re.sub(r"<description>.*?</description>", "<description>Allow NPM to Aster Voice streaming</description>", candidate, count=1, flags=re.S)

new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
new_rules = list(parsed.iter("rule"))
assert len(new_rules) == len(rules) + 1
created = next(rule for rule in new_rules if rule.get("uuid") == RULE_UUID)
assert matches(created, "9131")
print({"rule_uuid": RULE_UUID, "source": "192.168.50.23", "destination": "192.168.70.14:9131/TCP", "interface": created.findtext("interface"), "mode": "apply" if "--apply" in sys.argv else "dry-run"})

if "--apply" in sys.argv:
    backup = Path("/conf/backup") / ("config-aster-voice-stream-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml")
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.aster-voice-stream-candidate")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
