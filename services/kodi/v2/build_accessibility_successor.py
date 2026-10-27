"""Build the one-file reduced-motion successor for the accepted HP skin."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from accessibility import SETTING, reduced_motion


PREDECESSOR = "1bc4dac6ef5aee481b5bb20c1ae3872aec56117aa15351ac8bdb945815d099de"
RELATIVE = ".kodi/addons/skin.asterhome/1080i/Includes.xml"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build(source: Path, output: Path) -> str:
    if output.exists():
        raise ValueError("accessibility-successor-output")
    raw = source.read_bytes()
    if sha(raw) != PREDECESSOR:
        raise ValueError("accessibility-successor-predecessor")
    before = list(ET.fromstring(raw).iter("animation"))
    if not before or all(SETTING in (row.get("condition") or "") for row in before):
        raise ValueError("accessibility-successor-no-gap")
    changed = reduced_motion(raw)
    after = list(ET.fromstring(changed).iter("animation"))
    if len(after) != len(before) or not all(
            "!" + SETTING in (row.get("condition") or "") for row in after):
        raise ValueError("accessibility-successor-transform")
    payload = output / "payload" / RELATIVE
    payload.parent.mkdir(parents=True)
    payload.write_bytes(changed)
    helper = Path(__file__).with_name("tools") / "deploy_accessibility_successor.py"
    shutil.copyfile(helper, output / helper.name)
    manifest = {
        "schema": 1,
        "kind": "hp-accessibility-successor.v1",
        "file": {"path": RELATIVE, "before_sha256": PREDECESSOR,
                 "sha256": sha(changed)},
        "helper": {"path": helper.name, "sha256": sha(helper.read_bytes())},
    }
    rendered = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(rendered)
    return sha(rendered)
