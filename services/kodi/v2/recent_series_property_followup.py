"""Exact HP successor for resilient Recently Added series routing."""

from __future__ import annotations

import ast
import hashlib
import json


PREDECESSORS = {
    "plugin.py": "be9691ca82152739b8f1727eac6969f166cba6967e47c3eab1ba323edd620493",
    "launcher.py": "e2035c0a5689715015fc210ab3f50bb4c45d53b94aeb3e172c60f7677e8785b0",
    "family.json": "929b9312e5b17450fcbbbcc67b4b363e36416a733e0a011ba2b4bb680cbebd2c",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def plugin(raw):
    if sha(raw) != PREDECESSORS["plugin.py"]:
        raise ValueError("recent-property-plugin-predecessor")
    text = raw.decode()
    old = "            item.getVideoInfoTag().setDbId(row['id'])\n"
    new = old + "            item.setProperty('AsterDbId', str(row['id']))\n"
    if text.count(old) != 1:
        raise ValueError("recent-property-plugin-anchor")
    text = text.replace(old, new)
    ast.parse(text)
    return text.encode()


def launcher(raw):
    if sha(raw) != PREDECESSORS["launcher.py"]:
        raise ValueError("recent-property-launcher-predecessor")
    text = raw.decode()
    old = ("    identity=selected_show(window,control,xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBTYPE'),\n"
           "        xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBID'),\n")
    new = ("    identity_label=xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBID')\n"
           "    if not identity_label:\n"
           "        identity_label=xbmc.getInfoLabel('Container('+str(container)+').ListItem.Property(AsterDbId)')\n"
           "    identity=selected_show(window,control,xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBTYPE'),\n"
           "        identity_label,\n")
    if text.count(old) != 1:
        raise ValueError("recent-property-launcher-anchor")
    text = text.replace(old, new)
    ast.parse(text)
    return text.encode()


def family(raw, launcher_raw):
    if sha(raw) != PREDECESSORS["family.json"]:
        raise ValueError("recent-property-family-predecessor")
    value = json.loads(raw)
    path = "tools/aster_v2_series.py"
    if value["skin"].get(path) != PREDECESSORS["launcher.py"]:
        raise ValueError("recent-property-family-launcher")
    value["skin"][path] = sha(launcher_raw)
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
