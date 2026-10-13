"""Idempotently publish the private production Aster alias in OPNsense Unbound."""

import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path


CONFIG = Path("/conf/config.xml")
SOURCE_UUID = "d219ad4e-351a-420e-8bf7-509050af7ae9"
RULE_UUID = "b507a9f4-1478-4aef-b5db-94fb5b60d09e"
raw = CONFIG.read_text(encoding="utf-8")
root = ElementTree.fromstring(raw)
hosts = list(root.findall("./OPNsense/unboundplus/hosts/host"))
existing = [host for host in hosts if host.findtext("hostname") == "aster-voice"
            and host.findtext("domain") == "home.internal"]
if existing:
    if len(existing) != 1 or existing[0].findtext("server") != "192.168.20.37":
        raise RuntimeError("existing production Aster host override is inconsistent")
    print({"hostname": "aster-voice.home.internal", "address": "192.168.20.37",
           "mode": "present"})
    raise SystemExit(0)

source = next(host for host in hosts if host.get("uuid") == SOURCE_UUID)
if source.findtext("hostname") != "home" or source.findtext("domain") != "elliottrook.com":
    raise RuntimeError("Unbound reference host drifted")
match = re.search(r'<host uuid="' + re.escape(SOURCE_UUID) + r'">.*?</host>', raw, re.S)
if not match:
    raise RuntimeError("Unbound reference host XML is missing")
candidate = match.group().replace(SOURCE_UUID, RULE_UUID)
candidate = candidate.replace("<hostname>home</hostname>", "<hostname>aster-voice</hostname>")
candidate = candidate.replace("<domain>elliottrook.com</domain>", "<domain>home.internal</domain>")
candidate = candidate.replace("<server>192.168.50.23</server>", "<server>192.168.20.37</server>")
candidate = candidate.replace("<description>Homepage via Nginx Proxy Manager</description>",
                              "<description>Aster voice production direct private service</description>")
new = raw[:match.end()] + "\n          " + candidate + raw[match.end():]
parsed = ElementTree.fromstring(new)
if len(list(parsed.findall("./OPNsense/unboundplus/hosts/host"))) != len(hosts) + 1:
    raise RuntimeError("Unbound candidate host count is invalid")

apply = "--apply" in sys.argv
print({"hostname": "aster-voice.home.internal", "address": "192.168.20.37",
       "mode": "apply" if apply else "dry-run"})
if apply:
    backup = Path("/conf/backup") / (
        "config-aster-voice-prod-dns-before-" + time.strftime("%Y%m%d-%H%M%S") + ".xml"
    )
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(raw)
    metadata = CONFIG.stat()
    temporary = CONFIG.with_name("config.xml.aster-voice-prod-dns-candidate")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, CONFIG)
    print({"backup": str(backup), "reload_pending": True})
