"""Add the private recommendations hostname to OPNsense Unbound."""

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
SOURCE_UUID = "ae0a8c57-8e0d-491b-9f08-e43c1109aa67"
RULE_UUID = "d7e8f901-2345-4abc-8def-6789abcdef01"
raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
hosts = list(root.findall("./OPNsense/unboundplus/hosts/host"))
assert not any(host.get("uuid") == RULE_UUID for host in hosts), "host override already exists"
source = next(host for host in hosts if host.get("uuid") == SOURCE_UUID)
assert source.findtext("hostname") == "wiki" and source.findtext("server") == "192.168.50.23", "reference drift"
match = re.search(r'<host uuid="' + re.escape(SOURCE_UUID) + r'">.*?</host>', raw, re.S)
assert match, "reference host override XML missing"
candidate = match.group().replace(SOURCE_UUID, RULE_UUID)
candidate = candidate.replace("<hostname>wiki</hostname>", "<hostname>recommendations</hostname>")
candidate = candidate.replace("<description>Aster Knowledge Wiki via Nginx Proxy Manager</description>",
                              "<description>Unified Media Recommendations via Nginx Proxy Manager</description>")
new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
assert len(list(parsed.findall("./OPNsense/unboundplus/hosts/host"))) == len(hosts) + 1
print({"hostname": "recommendations.elliottrook.com", "address": "192.168.50.23",
       "mode": "apply" if "--apply" in sys.argv else "dry-run"})
if "--apply" in sys.argv:
    backup = Path("/conf/backup") / ("config-unified-media-dns-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml")
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.unified-media-dns-candidate")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
