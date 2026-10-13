"""Add the private portal hostname to a Pi-hole v6 dns.hosts list."""

import os
import shutil
from pathlib import Path


path = Path(os.environ.get("PIHOLE_CONFIG_PATH", "/opt/pihole/etc-pihole/pihole.toml"))
backup = path.with_name("pihole.toml.unified-media-before-20261006")
text = path.read_text(encoding="utf-8")
entry = '    "192.168.50.23 recommendations.elliottrook.com",'
if "recommendations.elliottrook.com" not in text:
    shutil.copy2(path, backup)
    anchor = '    "192.168.50.23 wiki.elliottrook.com",'
    if text.count(anchor) != 1:
        raise RuntimeError("expected unique wiki dns.hosts anchor is missing")
    temporary = path.with_name(path.name + ".unified-media.tmp")
    temporary.write_text(text.replace(anchor, anchor + "\n" + entry), encoding="utf-8")
    os.chmod(temporary, path.stat().st_mode & 0o777)
    temporary.replace(path)
print("unified-media-pihole=present")
