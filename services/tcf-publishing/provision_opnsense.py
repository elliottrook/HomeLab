"""Add the exact NPM-to-Content-Desk rule; dry-run unless --apply."""

import copy
import os
from pathlib import Path
import sys
import time
import uuid
import xml.etree.ElementTree as ElementTree

CONFIG = Path("/conf/config.xml")
SOURCE = "192.168.50.23"
DESTINATION = "192.168.20.35"
PORT = "8080"
DESCRIPTION = "NPM to dual-site photography Content Desk"

raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
rules = list(root.iter("rule"))
existing = next((rule for rule in rules if
                 rule.findtext("source_net") == SOURCE and
                 rule.findtext("destination_net") == DESTINATION and
                 rule.findtext("destination_port") == PORT), None)
if existing is not None:
    if existing.findtext("sequence") != "2194":
        raise SystemExit("existing Content Desk rule has unexpected sequence")
    print({"status": "present", "uuid": existing.get("uuid")})
    raise SystemExit(0)

reference = next(rule for rule in rules if
                 rule.findtext("source_net") == SOURCE and
                 rule.findtext("destination_net") == "192.168.20.34" and
                 rule.findtext("destination_port") == "8787")
parent = next(parent for parent in root.iter() if reference in list(parent))
candidate = copy.deepcopy(reference)
candidate.set("uuid", str(uuid.uuid4()))
candidate.find("destination_net").text = DESTINATION
candidate.find("destination_port").text = PORT
candidate.find("description").text = DESCRIPTION
sequence = 2194
candidate.find("sequence").text = str(sequence)
parent.insert(list(parent).index(reference) + 1, candidate)

print({"status": "apply" if "--apply" in sys.argv else "dry-run",
       "source": SOURCE, "destination": f"{DESTINATION}:{PORT}/TCP",
       "sequence": sequence, "uuid": candidate.get("uuid")})
if "--apply" in sys.argv:
    backup = Path("/conf/backup") / (
        "config-tcf-desk-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml"
    )
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.tcf-desk-candidate")
    tree = ElementTree.ElementTree(root)
    tree.write(temporary, encoding="unicode")
    os.chmod(temporary, metadata.st_mode & 0o777)
    os.chown(temporary, metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
