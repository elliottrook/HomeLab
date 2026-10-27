"""Consolidate the accepted final accessibility-bearing skin files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


SETTING = "Skin.HasSetting(AsterReducedMotion)"
FILES = {
    ".kodi/addons/skin.asterhome/1080i/Home.xml": "4c118dd42c3d97c1899a0dcbdce8e6ab42b22d3f309c09802f1a861fac9f830d",
    ".kodi/addons/skin.asterhome/1080i/Includes.xml": "c80a9842b11e1bd715e2df9bf2482093e76477420ec2cc21247269381a2e79aa",
    ".kodi/addons/skin.asterhome/1080i/IncludesHub.xml": "a06a827b489acf8ba557dabab6ee1f1092d632bbea758fbd4d6b8e0889fa95c1",
    ".kodi/addons/skin.asterhome/1080i/SkinSettings.xml": "94e0a2d63cad4fdedd8368f8367b1abfe5cce3cd6745eb06a7b5c7611e9e866b",
    ".kodi/addons/skin.asterhome/1080i/VideoOSD.xml": "19df16c15b7bee68384b2666067772371490e1a1bb8f44f1f3d2b4e685a5955c",
    ".kodi/addons/skin.asterhome/colors/Aster High Contrast.xml": "b11413e3a3dc5614f355f4eac434758b858cc215e5bdd53fbcee4c4d8d3dc39e",
}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path) -> None:
    for relative, wanted in FILES.items():
        path = root / relative
        if not path.is_file() or path.is_symlink() or sha(path) != wanted:
            raise ValueError("accessibility-final-file")
    for relative in ("Home.xml", "Includes.xml", "IncludesHub.xml", "VideoOSD.xml"):
        path = root / ".kodi/addons/skin.asterhome/1080i" / relative
        animations = list(ET.parse(path).iter("animation"))
        if not animations or not all("!" + SETTING in (row.get("condition") or "")
                                     for row in animations):
            raise ValueError("accessibility-final-motion")
    settings = ET.parse(root / ".kodi/addons/skin.asterhome/1080i/SkinSettings.xml")
    if len(settings.findall('.//control[@id="200"]')) != 1 \
            or len(settings.findall('.//control[@id="201"]')) != 1:
        raise ValueError("accessibility-final-settings")


def build(source: Path, output: Path) -> str:
    if output.exists(): raise ValueError("accessibility-final-output")
    validate(source)
    for relative in FILES:
        target = output / "payload" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    manifest = {"schema": 1, "kind": "hp-accessibility-final.v1",
                "files": [{"path": path, "sha256": digest}
                          for path, digest in sorted(FILES.items())]}
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()
