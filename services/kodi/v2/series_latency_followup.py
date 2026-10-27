"""Exact HP successor for responsive and consistent TV-series entry."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


PREDECESSORS = {
    "default.py": "1d5a4054321779b17bd8092b059ede232a5f24d7dbd0d68e72c324b64c4f1fa4",
    "component-manifest.json": "c89cea23ac882257838a8ee5d44c3b319a821c63b3a381c8847155f45986b9b5",
    "aster_v2_series.py": "c54b62d472dd276c09d0c6e6ce3134119e7a828c171b18aeb4f9ec5128142cab",
    "select_dispatch.py": "3ebd10d3cb447467fc4c66fd82386860e503221655e8ac4fe6905f656db7313d",
    "family-manifest.json": "ac0e0038b53a0c144c7867158b01aa7d93cb296c0009fb4b5f5e9ef5daf09c02",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(value, code):
    if not value:
        raise ValueError(code)


def runtime(raw, candidate):
    require(sha(raw) == PREDECESSORS["default.py"], "series-latency-runtime-predecessor")
    value = Path(candidate).read_bytes()
    ast.parse(value)
    require(b"queue_catalogue_art" in value and b"threading.Thread" in value
            and b"cache.localize(client.season" not in value,
            "series-latency-runtime-candidate")
    return value


def component(raw, runtime_raw):
    require(sha(raw) == PREDECESSORS["component-manifest.json"],
            "series-latency-component-predecessor")
    value = json.loads(raw)
    require(value.get("kind") == "hp-series-player" and len(value.get("files", [])) == 8,
            "series-latency-component-contract")
    row = next(item for item in value["files"] if item.get("path") == "default.py")
    require(row["sha256"] == PREDECESSORS["default.py"], "series-latency-component-runtime")
    row.update(bytes=len(runtime_raw), sha256=sha(runtime_raw))
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def launcher(raw, component_raw):
    require(sha(raw) == PREDECESSORS["aster_v2_series.py"],
            "series-latency-launcher-predecessor")
    text = raw.decode()
    old = "if window!=10025 or control!=50 or parent or kind!='tvshow':return None"
    new = ("if (window,control) not in ((10025,50),(10000,110)) or parent "
           "or kind!='tvshow':return None")
    require(text.count(old) == 1, "series-latency-launcher-route")
    text = text.replace(old, new)
    old_labels = ("identity=selected_show(window,control,xbmc.getInfoLabel('Container(50).ListItem.DBTYPE'),\n"
                  "        xbmc.getInfoLabel('Container(50).ListItem.DBID'),xbmc.getCondVisibility('Container(50).ListItem.IsParentFolder'))")
    new_labels = ("container=110 if (window,control)==(10000,110) else 50\n"
                  "    identity=selected_show(window,control,xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBTYPE'),\n"
                  "        xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBID'),\n"
                  "        xbmc.getCondVisibility('Container('+str(container)+').ListItem.IsParentFolder'))")
    require(text.count(old_labels) == 1, "series-latency-launcher-container")
    text = text.replace(old_labels, new_labels)
    old_pin = PREDECESSORS["component-manifest.json"]
    require(text.count(old_pin) == 1, "series-latency-launcher-pin")
    text = text.replace(old_pin, sha(component_raw))
    ast.parse(text)
    return text.encode()


def dispatcher(raw):
    require(sha(raw) == PREDECESSORS["select_dispatch.py"],
            "series-latency-dispatcher-predecessor")
    text = raw.decode()
    old = "if window_id == 10025 and focus_id == 50:"
    new = "if (window_id, focus_id) in ((10025, 50), (10000, 110)):"
    require(text.count(old) == 1, "series-latency-dispatcher-route")
    text = text.replace(old, new)
    ast.parse(text)
    return text.encode()


def family(raw, component_raw, launcher_raw, dispatcher_raw):
    require(sha(raw) == PREDECESSORS["family-manifest.json"],
            "series-latency-family-predecessor")
    value = json.loads(raw)
    record = value["components"]["aster-series-preview24"]
    require(record["manifest_sha256"] == PREDECESSORS["component-manifest.json"],
            "series-latency-family-component")
    require(value["skin"]["tools/aster_v2_series.py"] == PREDECESSORS["aster_v2_series.py"]
            and value["skin"]["tools/select_dispatch.py"] == PREDECESSORS["select_dispatch.py"],
            "series-latency-family-routes")
    record["manifest_sha256"] = sha(component_raw)
    value["skin"]["tools/aster_v2_series.py"] = sha(launcher_raw)
    value["skin"]["tools/select_dispatch.py"] = sha(dispatcher_raw)
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
