#!/usr/bin/env python3
"""Build a direct-launch, HP-only Aster Books compiler beta runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).parents[1]
KODI = ROOT / "kodi"
sys.path.insert(0, str(ROOT))

from epub_narration.publication import sha256_file


def _layout():
    root = ET.Element("window")
    ET.SubElement(root, "defaultcontrol", always="true").text = "500"
    ET.SubElement(root, "backgroundcolor").text = "ff171a18"
    controls = ET.SubElement(root, "controls")

    def control(kind, identity, left, top, width, height, **fields):
        node = ET.SubElement(controls, "control", type=kind, id=str(identity))
        for key, value in dict(left=left, top=top, width=width, height=height, **fields).items():
            ET.SubElement(node, key).text = str(value)
        return node

    control("label", 11, 110, 60, 1500, 60, label="Aster Books · Compiler beta", font="font40", textcolor="fff3eee5")
    control("label", 12, 110, 125, 1500, 42, label="HP Lab · Private direct launch", font="font20", textcolor="ffc2a06b")
    for size, identity in ((24, 501), (30, 502), (40, 503)):
        control("textbox", identity, 220, 205, 1480, 650, label="", font="font" + str(size), textcolor="fff3eee5",
                visible="String.IsEqual(Window.Property(Books.Size" + str(size) + "),true)")
    control("button", 500, 220, 205, 1480, 650, label="", textcolor="00000000", focusedcolor="00000000",
            texturefocus="", texturenofocus="", onup=201, ondown=201)
    control("label", 520, 220, 870, 1480, 42, label="$INFO[Window.Property(Books.Status)]", font="font24", textcolor="ffc2a06b")
    buttons = (
        (201, 220, 190, "Play / pause", 207, 202),
        (202, 425, 120, "Stop", 201, 203),
        (203, 560, 220, "Previous chapter", 202, 204),
        (204, 795, 190, "Next chapter", 203, 205),
        (205, 1000, 210, "Restart chapter", 204, 206),
        (206, 1225, 230, "Clear beta progress", 205, 207),
        (207, 1470, 150, "Text 30", 206, 201),
    )
    for identity, left, width, label, prior, following in buttons:
        node = control("button", identity, left, 945, width, 62, label=label, font="font20", textcolor="fff3eee5",
                       focusedcolor="ff171a18", align="center", aligny="center", texturenofocus="",
                       onleft=prior, onright=following, onup=500, ondown=500)
        ET.SubElement(node, "texturefocus", border="18", colordiffuse="ffc2a06b").text = "special://skin/media/ui-panel.png"
    control("label", 530, 220, 1025, 1480, 35,
            label="Back stops only this beta and saves private progress · No autoplay · Gold marks the current sentence",
            font="font20", textcolor="ff9b9d95")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def build(output: Path) -> str:
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    files = {
        "default.py": (KODI / "default.py").read_bytes(),
        "kodi_port.py": (KODI / "kodi_port.py").read_bytes(),
        "reader_pages.py": (KODI / "reader_pages.py").read_bytes(),
        "resources/skins/Default/1080i/AsterBooksCompiler.xml": _layout(),
    }
    for name in ("__init__.py", "publication.py", "aster_books.py"):
        files["runtime/epub_narration/" + name] = (ROOT / "epub_narration" / name).read_bytes()
    for relative, raw in files.items():
        path = output / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o600)
    manifest = {
        "schema": 1,
        "kind": "aster-books-compiler-hp-beta-v1",
        "hp_only": True,
        "active": True,
        "normal_entry": False,
        "network": False,
        "shared_progress": False,
        "files": {name: sha256_file(output / name) for name in sorted(files)},
    }
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "bundle.json").write_bytes(raw)
    (output / "bundle.json").chmod(0o600)
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.output))
