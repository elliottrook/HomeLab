"""Idempotently add the two LAN-only photography review aliases to Unbound."""

import copy
import os
import sys
import time
import uuid
import xml.etree.ElementTree as ElementTree
from pathlib import Path

CONFIG = Path("/conf/config.xml")
NAMES = ("contrast", "closet")
raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
hosts_parent = root.find("./OPNsense/unboundplus/hosts")
if hosts_parent is None:
    raise RuntimeError("Unbound host collection missing")
hosts = list(hosts_parent.findall("host"))
reference = next(host for host in hosts if host.findtext("hostname") == "wiki"
                 and host.findtext("domain") == "elliottrook.com"
                 and host.findtext("server") == "192.168.50.23")
added = []
for name in NAMES:
    matching = [host for host in hosts if host.findtext("hostname") == name
                and host.findtext("domain") == "elliottrook.com"]
    if matching:
        if len(matching) != 1 or matching[0].findtext("server") != "192.168.50.23":
            raise RuntimeError(f"existing {name} override is inconsistent")
        continue
    candidate = copy.deepcopy(reference)
    candidate.set("uuid", str(uuid.uuid4()))
    candidate.find("hostname").text = name
    candidate.find("description").text = f"Private photography review: {name}"
    hosts_parent.append(candidate)
    added.append(name)

print({"aliases": list(NAMES), "address": "192.168.50.23",
       "added": added, "mode": "apply" if "--apply" in sys.argv else "dry-run"})
if added and "--apply" in sys.argv:
    backup = Path("/conf/backup") / (
        "config-tcf-private-sites-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml")
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.tcf-private-sites-candidate")
    ElementTree.ElementTree(root).write(temporary, encoding="unicode")
    os.chmod(temporary, metadata.st_mode & 0o777)
    os.chown(temporary, metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
