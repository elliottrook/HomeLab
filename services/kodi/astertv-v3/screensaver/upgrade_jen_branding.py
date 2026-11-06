#!/usr/bin/env python3
"""Exact-hash SA-M9-JEN upgrade from generic to section-aware branding."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

from install_jen_canary import NEW_ID, HOST, selected_screensaver, verify_payload


EXPECTED_CURRENT = {
    "addon.xml": "af7913d8630d22bfa83f35a549bbf504df7d14df685aa0ff9877c76e29ef496f",
    "default.py": "ce7006251e042b9c0548fbb233d99cd83ea345be31b37cda410eaae843682107",
    "policy.py": "6a02c678e02cd4b3e7d2c6b893dba765bb6411f746f613e03079428574735a99",
    "service.py": "8453ad5d93d997e027d49d556670f979910e4e81afebd236f3381b7768981963",
    "resources/skins/Default/1080i/AsterIdle.xml":
        "34a95c157dbe15ce64ff40c301214f47a520f03bee24213b3ad69a1324a327be",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state(name: str) -> str:
    return subprocess.run(("systemctl", "is-active", name), check=False,
                          text=True, capture_output=True).stdout.strip()


def upgrade(staged: Path, storage: Path) -> dict:
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-host")
    verify_payload(staged)
    addons = storage / ".kodi/addons"
    userdata = storage / ".kodi/userdata"
    target = addons / NEW_ID
    temporary = addons / (NEW_ID + ".asternew")
    displaced = addons / (NEW_ID + ".asterold")
    settings = userdata / "guisettings.xml"
    for relative, expected in EXPECTED_CURRENT.items():
        if sha256(target / relative) != expected:
            raise RuntimeError("current-canary-drift:" + relative)
    if selected_screensaver(settings) != NEW_ID:
        raise RuntimeError("v3-not-selected")
    if temporary.exists() or displaced.exists():
        raise RuntimeError("stale-upgrade-directory")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    checkpoint = storage / ".aster-checkpoints" / ("astertv-v3-m9-branding-" + stamp)
    checkpoint.mkdir(parents=True, mode=0o700)
    stopped = False
    moved = False
    swapped = False
    try:
        subprocess.run(("systemctl", "stop", "kodi"), check=True)
        stopped = True
        if state("kodi") != "inactive":
            raise RuntimeError("kodi-did-not-stop")
        shutil.copytree(target, checkpoint / NEW_ID)
        shutil.copy2(settings, checkpoint / "guisettings.xml")
        log = storage / ".kodi/temp/kodi.log"
        if log.exists():
            shutil.copy2(log, checkpoint / "kodi.log")
        (checkpoint / "state.json").write_text(json.dumps({
            "schema_version": 1, "host": HOST, "selected": NEW_ID,
            "old_files": EXPECTED_CURRENT,
            "new_manifest_sha256": sha256(staged / "manifest.json"),
        }, indent=2, sort_keys=True) + "\n")

        shutil.copytree(staged / NEW_ID, temporary)
        os.rename(target, displaced)
        moved = True
        os.rename(temporary, target)
        swapped = True
        subprocess.run(("systemctl", "start", "kodi"), check=True)
        stopped = False
        time.sleep(10)
        if state("kodi") != "active":
            raise RuntimeError("kodi-not-active-after-upgrade")
        if selected_screensaver(settings) != NEW_ID:
            raise RuntimeError("v3-selection-not-retained")
        record = verify_payload(staged)
        for row in record["files"]:
            if sha256(target / row["path"]) != row["sha256"]:
                raise RuntimeError("deployed-payload-drift:" + row["path"])
        shutil.rmtree(displaced)
        return {"outcome": "upgraded", "checkpoint": str(checkpoint),
                "selected": NEW_ID, "manifest": sha256(staged / "manifest.json")}
    except Exception:
        if not stopped:
            subprocess.run(("systemctl", "stop", "kodi"), check=False)
        if swapped:
            if target.exists():
                shutil.rmtree(target)
            if displaced.exists():
                os.rename(displaced, target)
        elif moved and displaced.exists() and not target.exists():
            os.rename(displaced, target)
        if temporary.exists():
            shutil.rmtree(temporary)
        subprocess.run(("systemctl", "start", "kodi"), check=False)
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", type=Path, required=True)
    parser.add_argument("--storage", type=Path, default=Path("/storage"))
    args = parser.parse_args(argv)
    print(json.dumps(upgrade(args.staged, args.storage), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

