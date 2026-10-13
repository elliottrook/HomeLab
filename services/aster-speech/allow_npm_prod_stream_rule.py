"""Allow only NPM to reach the production Aster canonical streaming API."""

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
SOURCE_UUID = "c69d946a-f769-4cdf-8bb8-29aa34ae4529"
RULE_UUID = "a8d3a7b1-221e-4c80-a03c-0124e52baf10"
SOURCE = "192.168.50.23"
DESTINATION = "192.168.20.37"
PORT = "9131"

raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))


def matches(rule: ElementTree.Element, destination: str) -> bool:
    expected = {
        "source_net": SOURCE,
        "destination_net": destination,
        "destination_port": PORT,
        "protocol": "TCP",
        "action": "pass",
        "enabled": "1",
        "quick": "1",
    }
    return all(rule.findtext(key) == value for key, value in expected.items())


existing = [rule for rule in rules if rule.get("uuid") == RULE_UUID]
if existing:
    if len(existing) != 1 or not matches(existing[0], DESTINATION):
        raise RuntimeError("existing production NPM rule drifted")
    print({"rule_uuid": RULE_UUID, "status": "already-present"})
    raise SystemExit(0)

reference = [rule for rule in rules if rule.get("uuid") == SOURCE_UUID]
if len(reference) != 1 or not matches(reference[0], "192.168.70.14"):
    raise RuntimeError("accepted lab NPM streaming rule is missing or drifted")
match = re.search(r'<rule uuid="' + re.escape(SOURCE_UUID) + r'">.*?</rule>', raw, re.S)
if not match:
    raise RuntimeError("accepted lab NPM rule XML is missing")
candidate = match.group().replace(SOURCE_UUID, RULE_UUID, 1)
candidate = candidate.replace(
    "<destination_net>192.168.70.14</destination_net>",
    f"<destination_net>{DESTINATION}</destination_net>",
)
candidate = re.sub(
    r"<description>.*?</description>",
    "<description>Allow NPM to Aster Voice production streaming</description>",
    candidate,
    count=1,
    flags=re.S,
)
new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
new_rules = list(parsed.iter("rule"))
if len(new_rules) != len(rules) + 1:
    raise RuntimeError("candidate firewall rule count is invalid")
created = next(rule for rule in new_rules if rule.get("uuid") == RULE_UUID)
if not matches(created, DESTINATION):
    raise RuntimeError("candidate production NPM rule is invalid")

apply = "--apply" in sys.argv
print({"rule_uuid": RULE_UUID, "source": SOURCE,
       "destination": f"{DESTINATION}:{PORT}/TCP",
       "interface": created.findtext("interface"),
       "mode": "apply" if apply else "dry-run"})
if apply:
    backup = Path("/conf/backup") / (
        "config-aster-voice-prod-npm-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml"
    )
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.aster-voice-prod-npm-candidate")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
