#!/usr/bin/env python3
"""Render a physical equipment keymap only from an accepted capture record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


CONTROLS = ("volume_up", "volume_down", "mute_toggle", "power_toggle")
RESERVED = frozenset({
    "select", "return", "enter", "browser_back", "backspace", "escape",
    "up", "down", "left", "right",
})
RUN = "RunScript(special://home/addons/service.asterremote/equipment.py,{})"


def validate(value: dict) -> dict[str, dict]:
    if value.get("schema_version") != 1 or value.get("kind") != "astertv-physical-equipment-keys":
        raise ValueError("capture-schema")
    if value.get("hostname") not in {"AsterTV-Family", "AsterTV-Bedroom"}:
        raise ValueError("capture-host")
    bindings = value.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(CONTROLS):
        raise ValueError("capture-controls")
    seen = set()
    for control, row in bindings.items():
        if not isinstance(row, dict) or set(row) != {"kind", "value"}:
            raise ValueError("capture-binding")
        kind, raw = row["kind"], row["value"]
        if kind == "named":
            if not isinstance(raw, str) or not re.fullmatch(r"[a-z][a-z0-9_]{1,31}", raw):
                raise ValueError("capture-key-name")
            if raw in RESERVED:
                raise ValueError("capture-reserved-key")
            identity = (kind, raw)
        elif kind == "id":
            if not isinstance(raw, int) or isinstance(raw, bool) or not 1 <= raw <= 65535:
                raise ValueError("capture-key-id")
            identity = (kind, raw)
        else:
            raise ValueError("capture-key-kind")
        if identity in seen:
            raise ValueError("capture-duplicate-key")
        seen.add(identity)
    return bindings


def render(value: dict) -> bytes:
    bindings = validate(value)
    root = ET.Element("keymap")
    keyboard = ET.SubElement(ET.SubElement(ET.SubElement(root, "global"), "keyboard"), "bindings")
    # The wrapper is removed before serialization so ElementTree cannot merge
    # captured names with structural nodes.
    global_keyboard = root.find("./global/keyboard")
    global_keyboard.remove(keyboard)
    for control in CONTROLS:
        row = bindings[control]
        if row["kind"] == "named":
            node = ET.SubElement(global_keyboard, row["value"])
        else:
            node = ET.SubElement(global_keyboard, "key", {"id": str(row["value"])})
        node.text = RUN.format(control)
    ET.indent(root, space="  ")
    return b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    args.output.write_bytes(render(json.loads(args.capture.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
