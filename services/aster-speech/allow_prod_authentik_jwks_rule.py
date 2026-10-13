"""Allow only production Aster Voice to fetch Authentik JWKS over NPM HTTPS."""

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
SOURCE_UUID = "67302b29-9f46-413a-8753-c791ef3a9070"
RULE_UUID = "ee51eb3d-8d64-41af-a831-f4bff36dcba2"
SOURCE = "192.168.20.37"
DESTINATION = "192.168.50.23"
PORT = "443"

raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))


def matches(rule: ElementTree.Element, source: str) -> bool:
    expected = {
        "source_net": source,
        "destination_net": DESTINATION,
        "destination_port": PORT,
        "protocol": "TCP",
        "action": "pass",
        "enabled": "1",
        "quick": "1",
        "interface": "opt3",
    }
    return all(rule.findtext(key) == value for key, value in expected.items())


existing = [rule for rule in rules if rule.get("uuid") == RULE_UUID]
if existing:
    if len(existing) != 1 or not matches(existing[0], SOURCE):
        raise RuntimeError("existing production JWKS rule drifted")
    print({"rule_uuid": RULE_UUID, "status": "already-present"})
    raise SystemExit(0)

reference = [rule for rule in rules if rule.get("uuid") == SOURCE_UUID]
if len(reference) != 1 or not matches(reference[0], "192.168.20.32"):
    raise RuntimeError("same-VLAN NetBox Authentik reference rule is missing or drifted")
match = re.search(r'<rule uuid="' + re.escape(SOURCE_UUID) + r'">.*?</rule>', raw, re.S)
if not match:
    raise RuntimeError("reference Authentik rule XML is missing")
candidate = match.group().replace(SOURCE_UUID, RULE_UUID, 1)
candidate = candidate.replace(
    "<source_net>192.168.20.32</source_net>",
    f"<source_net>{SOURCE}</source_net>",
)
candidate = re.sub(
    r"<description>.*?</description>",
    "<description>Allow Aster Voice production to Authentik JWKS via NPM</description>",
    candidate,
    count=1,
    flags=re.S,
)
new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
new_rules = list(parsed.iter("rule"))
if len(new_rules) != len(rules) + 1:
    raise RuntimeError("candidate JWKS rule count is invalid")
created = next(rule for rule in new_rules if rule.get("uuid") == RULE_UUID)
if not matches(created, SOURCE):
    raise RuntimeError("candidate production JWKS rule is invalid")

apply = "--apply" in sys.argv
print({"rule_uuid": RULE_UUID, "source": SOURCE,
       "destination": f"{DESTINATION}:{PORT}/TCP", "interface": "opt3",
       "mode": "apply" if apply else "dry-run"})
if apply:
    backup = Path("/conf/backup") / (
        "config-aster-voice-prod-jwks-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml"
    )
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.aster-voice-prod-jwks-candidate")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
