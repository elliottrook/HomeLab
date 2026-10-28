#!/usr/bin/env python3
"""Add only a Kodi 22 Back adapter to the released YouTube navigation."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path("/storage")
SKIN = ROOT / ".kodi/addons/skin.asterhome"
HOME = SKIN / "1080i/Home.xml"
NAV = SKIN / "1080i/MyVideoNav.xml"
HELPER = SKIN / "tools/youtube_back.py"
HELPER_SOURCE = Path("/tmp/aster-youtube-back.py")
KEYMAP = ROOT / ".kodi/userdata/keymaps/g20s-pro-plus.xml"
FAMILY = ROOT / ".kodi/addons/script.asterruntime/family-manifest.json"
CHECKPOINT = ROOT / ".aster-checkpoints/aster-youtube-production-navigation2"
BACK_ACTION = "RunScript(special://home/addons/skin.asterhome/tools/youtube_back.py)"
PREDECESSOR = {
    "home": "a8e4b03c4aa6f2df64bf0bd5ad54edccd1968d63960c1ca767fb7b67a12fda76",
    "nav": "be3b348385815e2812044ce843315ae885a4e92aa4048269ef1da5daf883cbdc",
    "keymap": "1c3661aa1c9109b9390b9004203ce6cbe53d03d559f88a019db01d22a430d2c1",
    "family": "103449f1d38a75d2b2469fadb097b140160a18d30ce0890aed1de8281bdac4dd",
    "helper_source": "3b01bfc1771d3aa53d7eb121295497dad9e0b539620889052d5f62b0fb8ff8cf",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def require(value, code):
    if not value:
        raise RuntimeError(code)


def atomic(path, raw, mode=None):
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-youtube-navigation-",
                                             dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode if mode is not None else 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def candidates(home_before, nav_before, keymap_before, family_before, helper):
    home_after = home_before

    nav = ET.fromstring(nav_before)
    require(nav.find(".//control[@id='9530']") is not None
            and nav.find(".//control[@id='9531']") is not None
            and nav.find(".//control[@id='9532']") is not None,
            "youtube-navigation-dedicated-controls")
    for identity in (9305, 9404):
        node = nav.find(f".//control[@id='{identity}']")
        action = node.find("onclick") if node is not None else None
        require(action is not None and action.text == "Action(Back)",
                f"youtube-navigation-back-predecessor:{identity}")
        action.text = BACK_ACTION
    nav_after = ET.tostring(nav, encoding="utf-8", xml_declaration=True)

    keymap = ET.fromstring(keymap_before)
    require(keymap.find("MyVideoNav") is None, "youtube-navigation-keymap-predecessor")
    window = ET.SubElement(keymap, "MyVideoNav")
    keyboard = ET.SubElement(window, "keyboard")
    for name in ("escape", "backspace", "browser_back"):
        ET.SubElement(keyboard, name).text = BACK_ACTION
    mouse = ET.SubElement(window, "mouse")
    ET.SubElement(mouse, "rightclick").text = BACK_ACTION
    keymap_after = ET.tostring(keymap, encoding="utf-8", xml_declaration=True)

    family = json.loads(family_before)
    require(family["skin"]["1080i/Home.xml"] == sha(home_before)
            and "1080i/MyVideoNav.xml" not in family["skin"],
            "youtube-navigation-family-predecessor")
    family["skin"]["1080i/Home.xml"] = sha(home_after)
    family["skin"]["1080i/MyVideoNav.xml"] = sha(nav_after)
    family["skin"]["tools/youtube_back.py"] = sha(helper)
    return home_after, nav_after, keymap_after, encoded(family)


def main():
    require(os.uname().nodename == "AsterTVProd", "production-only")
    require(not CHECKPOINT.exists() and not HELPER.exists(),
            "youtube-navigation-boundary")
    require(HELPER_SOURCE.is_file() and not HELPER_SOURCE.is_symlink(),
            "youtube-navigation-helper-source")
    before = {
        "home": HOME.read_bytes(), "nav": NAV.read_bytes(),
        "keymap": KEYMAP.read_bytes(), "family": FAMILY.read_bytes(),
    }
    helper = HELPER_SOURCE.read_bytes()
    require(all(sha(before[name]) == PREDECESSOR[name] for name in before)
            and sha(helper) == PREDECESSOR["helper_source"],
            "youtube-navigation-live-predecessor")
    home, nav, keymap, family = candidates(
        before["home"], before["nav"], before["keymap"], before["family"], helper)
    after = {"home": home, "nav": nav, "keymap": keymap,
             "family": family, "helper": helper}
    targets = {"home": HOME, "nav": NAV, "keymap": KEYMAP,
               "family": FAMILY, "helper": HELPER}
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for name, raw in before.items():
        path = CHECKPOINT / "before" / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_bytes(raw)
    (CHECKPOINT / "state.json").write_text('{"state":"prepared"}\n')
    try:
        for name, raw in after.items():
            atomic(targets[name], raw, 0o755 if name == "helper" else 0o644)
        require(all(targets[name].read_bytes() == raw for name, raw in after.items()),
                "youtube-navigation-install")
        evidence = {name + "_sha256": sha(raw) for name, raw in after.items()}
        (CHECKPOINT / "manifest.json").write_text(json.dumps(
            {"before": PREDECESSOR, "after": evidence,
             "design": "Released dedicated controls plus bounded Kodi 22 Back adapter; Home unchanged"},
            indent=2, sort_keys=True) + "\n")
        (CHECKPOINT / "state.json").write_text('{"state":"installed"}\n')
    except Exception:
        for name, raw in before.items():
            atomic(targets[name], raw)
        if HELPER.exists():
            HELPER.unlink()
        (CHECKPOINT / "state.json").write_text('{"state":"rolled-back"}\n')
        raise
    print(json.dumps({"installed": True, **evidence}, sort_keys=True))


if __name__ == "__main__":
    main()
