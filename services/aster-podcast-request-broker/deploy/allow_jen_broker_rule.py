#!/usr/bin/env python3
"""Add only AsterTV-Jen TCP access to the podcast request broker."""

from __future__ import annotations

import os
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as ElementTree


CONFIG = Path("/conf/config.xml")
REFERENCE_UUID = "8cb0da40-9b94-4b02-8167-2895b8881e30"
RULE_UUID = "1b69df39-29d6-4d36-b382-fb3a255e22dd"
SEQUENCE = "3096"
SOURCE = "192.168.1.180"
DESTINATION = "192.168.20.40"
PORT = "8790"
DESCRIPTION = "AsterTV-Jen podcast request queue broker"


raw = CONFIG.read_text()
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))
if any(rule.get("uuid") == RULE_UUID for rule in rules):
    raise RuntimeError("podcast-rule-already-exists")
if any(rule.findtext("sequence") == SEQUENCE for rule in rules):
    raise RuntimeError("podcast-rule-sequence-in-use")
match = re.search(r'<rule uuid="' + REFERENCE_UUID + r'">.*?</rule>', raw, re.S)
if not match:
    raise RuntimeError("podcast-reference-rule-missing")
candidate = match.group().replace(REFERENCE_UUID, RULE_UUID, 1)
for field, value in (("sequence", SEQUENCE), ("source_net", SOURCE),
                     ("destination_net", DESTINATION), ("destination_port", PORT),
                     ("description", DESCRIPTION)):
    candidate, count = re.subn(rf"<{field}>.*?</{field}>",
                               f"<{field}>{value}</{field}>", candidate, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("podcast-reference-field-" + field)
new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
created = [rule for rule in parsed.iter("rule") if rule.get("uuid") == RULE_UUID]
if len(created) != 1 or created[0].findtext("source_net") != SOURCE \
        or created[0].findtext("destination_port") != PORT:
    raise RuntimeError("podcast-rule-validation")
print({"mode": "apply" if "--apply" in sys.argv else "dry-run", "uuid": RULE_UUID,
       "source": SOURCE, "destination": DESTINATION, "port": PORT})
if "--apply" in sys.argv:
    backup = Path("/conf/backup") / ("config-astertv-jen-podcast-before-" +
                                     time.strftime("%Y%m%d-%H%M%S") + ".xml")
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.astertv-podcast-candidate")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(new); stream.flush(); os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
