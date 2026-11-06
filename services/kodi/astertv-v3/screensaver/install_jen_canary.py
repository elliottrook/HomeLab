#!/usr/bin/env python3
"""Host-bound, checkpointed installer for the authorized SA-M9-JEN canary."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import time
import xml.etree.ElementTree as ET


HOST = "AsterTV-Jen"
OLD_ID = "screensaver.asterhome.v2lab"
NEW_ID = "screensaver.asterhome.v3"
EXPECTED_OLD = {
    "default.py": "9a52adbcd7165e270831d290d067ba98903e0c13b9fd9e3089c2567d9c7568e4",
    "addon.xml": "63961dc00f6044bba6007f199032704c0cd0f39b2638222d37ad4dc6ed807a21",
    "resources/skins/Default/1080i/AsterIdle.xml":
        "ebf9180d0c0e16874600c4ff9e89c180ceb32ba0f501e298365f56cd5d741a7b",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, text=True, capture_output=True)


def unit_state(name: str) -> str:
    return subprocess.run(("systemctl", "is-active", name), check=False,
                          text=True, capture_output=True).stdout.strip()


def verify_payload(staged: Path) -> dict:
    manifest_path = staged / "manifest.json"
    record = json.loads(manifest_path.read_text())
    if record.get("identity") != NEW_ID or record.get("release") is not False:
        raise RuntimeError("candidate-manifest-boundary")
    addon = staged / NEW_ID
    declared = []
    for row in record.get("files", []):
        relative = row["path"]
        path = addon / relative
        if not path.is_file() or sha256(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
            raise RuntimeError("candidate-payload-drift:" + relative)
        declared.append(relative)
    actual = sorted(str(path.relative_to(addon)) for path in addon.rglob("*") if path.is_file())
    if sorted(declared) != actual:
        raise RuntimeError("candidate-file-inventory-drift")
    return record


def selected_screensaver(settings: Path) -> str:
    root = ET.parse(settings).getroot()
    node = root.find(".//setting[@id='screensaver.mode']")
    return (node.text or "") if node is not None else ""


def set_screensaver(settings: Path, identity: str) -> None:
    data = settings.read_text()
    pattern = r'(<setting id="screensaver\.mode"[^>]*>)[^<]*(</setting>)'
    updated, count = re.subn(pattern, r"\g<1>" + identity + r"\g<2>", data)
    if count != 1:
        raise RuntimeError("screensaver-setting-missing")
    temporary = settings.with_suffix(".xml.astertmp")
    temporary.write_text(updated)
    os.replace(temporary, settings)


def install(staged: Path, storage: Path) -> dict:
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-host")
    verify_payload(staged)
    addons = storage / ".kodi/addons"
    userdata = storage / ".kodi/userdata"
    settings = userdata / "guisettings.xml"
    database = sorted((userdata / "Database").glob("Addons*.db"))[-1]
    old = addons / OLD_ID
    new = addons / NEW_ID
    for relative, expected in EXPECTED_OLD.items():
        if sha256(old / relative) != expected:
            raise RuntimeError("v2-baseline-drift:" + relative)
    if selected_screensaver(settings) != OLD_ID:
        raise RuntimeError("unexpected-current-screensaver")
    if new.exists():
        raise RuntimeError("v3-target-already-exists")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    checkpoint = storage / ".aster-checkpoints" / ("astertv-v3-m9-jen-" + stamp)
    checkpoint.mkdir(parents=True, mode=0o700)
    stopped = False
    changed = False
    try:
        run("systemctl", "stop", "kodi")
        stopped = True
        if unit_state("kodi") != "inactive":
            raise RuntimeError("kodi-did-not-stop")
        shutil.copy2(settings, checkpoint / "guisettings.xml")
        shutil.copy2(database, checkpoint / database.name)
        log = storage / ".kodi/temp/kodi.log"
        if log.exists():
            shutil.copy2(log, checkpoint / "kodi.log")
        (checkpoint / "state.json").write_text(json.dumps({
            "schema_version": 1, "host": HOST, "old_id": OLD_ID,
            "new_id": NEW_ID, "new_preexisted": False,
            "guisettings_sha256": sha256(settings),
            "database": database.name, "database_sha256": sha256(database),
        }, indent=2, sort_keys=True) + "\n")

        changed = True
        shutil.copytree(staged / NEW_ID, new)
        set_screensaver(settings, NEW_ID)
        with sqlite3.connect(database) as connection:
            connection.execute(
                "INSERT INTO installed(addonID,enabled,installDate,origin,disabledReason) "
                "VALUES(?,1,datetime('now'),'system',0) "
                "ON CONFLICT(addonID) DO UPDATE SET enabled=1,disabledReason=0",
                (NEW_ID,),
            )
        run("systemctl", "start", "kodi")
        stopped = False
        time.sleep(10)
        if unit_state("kodi") != "active":
            raise RuntimeError("kodi-not-active-after-install")
        if selected_screensaver(settings) != NEW_ID:
            raise RuntimeError("v3-selection-not-retained")
        log_text = (storage / ".kodi/temp/kodi.log").read_text(errors="replace")
        if "Found addon: 'screensaver.asterhome.v3 v0.1.0'" not in log_text:
            raise RuntimeError("v3-addon-not-discovered")
        if "screensaver.asterhome.v3" in log_text and "ERROR" in "\n".join(
                line for line in log_text.splitlines() if "screensaver.asterhome.v3" in line):
            raise RuntimeError("v3-addon-log-error")
        return {"outcome": "installed", "checkpoint": str(checkpoint),
                "selected": NEW_ID, "manifest": sha256(staged / "manifest.json")}
    except Exception:
        if changed:
            try:
                if not stopped:
                    subprocess.run(("systemctl", "stop", "kodi"), check=False)
                shutil.copy2(checkpoint / "guisettings.xml", settings)
                shutil.copy2(checkpoint / database.name, database)
                if new.exists():
                    shutil.rmtree(new)
            finally:
                subprocess.run(("systemctl", "start", "kodi"), check=False)
        elif stopped:
            subprocess.run(("systemctl", "start", "kodi"), check=False)
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", type=Path, required=True)
    parser.add_argument("--storage", type=Path, default=Path("/storage"))
    args = parser.parse_args(argv)
    print(json.dumps(install(args.staged, args.storage), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

