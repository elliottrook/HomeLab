#!/usr/bin/env python3
"""Install and enforce AsterTV-Jen's low-spec Jellyfin playback policy.

The policy is deliberately client-side and host-bound.  It keeps HEVC direct
play for media no wider than 1920 pixels, caps the client request at 18 Mb/s,
and makes Jellyfin transcode wider HEVC media.  An unreviewed Jellyfin add-on
update fails safe by selecting the add-on's supported "transcode all HEVC"
setting until its code has been reviewed and added to this installer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


HOST = "AsterTV-Jen"
UPSTREAM_SHA256 = "6c44e9df8e28888968455564b6496003bd3a32d2efd65bf1dd6b19c104ec817b"
MAX_BITRATE_INDEX = "16"  # Jellyfin for Kodi index 16 = 18,000 kb/s.
POLICY_DIR = Path("/storage/.aster-policy")
STATE_NAME = "jellyfin-client-policy.json"
STATUS_NAME = "jellyfin-client-policy-status.json"
ADDON_REL = Path(".kodi/addons/plugin.video.jellyfin/jellyfin_kodi/helper/playutils.py")
SETTINGS_REL = Path(".kodi/userdata/addon_data/plugin.video.jellyfin/settings.xml")
UNIT_DIR_REL = Path(".config/system.d")
SCRIPT_NAME = "jellyfin_client_policy.py"
SERVICE_NAME = "astertv-jen-jellyfin-policy.service"
PATH_NAME = "astertv-jen-jellyfin-policy.path"

PROFILE_ANCHOR = b'''        if settings("transcodeHi10P.bool"):\n'''
PROFILE_POLICY = b'''        # ASTERTV-JEN-LOW-SPEC-HEVC-POLICY\n        profile["CodecProfiles"].append(\n            {\n                "Type": "Video",\n                "codec": "hevc",\n                "Conditions": [\n                    {\n                        "Condition": "LessThanEqual",\n                        "Property": "Width",\n                        "Value": "1920",\n                    }\n                ],\n            }\n        )\n\n'''

SERVICE = """[Unit]
Description=Enforce AsterTV-Jen low-spec Jellyfin client policy
After=local-fs.target astertv-release-guard.service
Before=kodi.service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /storage/.aster-policy/jellyfin_client_policy.py reconcile

[Install]
WantedBy=kodi.service
"""

PATH_UNIT = """[Unit]
Description=Watch AsterTV-Jen Jellyfin client policy inputs
After=local-fs.target

[Path]
PathChanged=/storage/.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/helper/playutils.py
PathChanged=/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/settings.xml
Unit=astertv-jen-jellyfin-policy.service

[Install]
WantedBy=multi-user.target
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, candidate = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(candidate, mode)
        os.replace(candidate, path)
    finally:
        try:
            os.unlink(candidate)
        except FileNotFoundError:
            pass


def paths(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    storage = root / "storage" if root != Path("/") else Path("/storage")
    policy = storage / POLICY_DIR.relative_to("/storage")
    return (
        storage / ADDON_REL,
        storage / SETTINGS_REL,
        policy / STATE_NAME,
        policy / STATUS_NAME,
        storage / UNIT_DIR_REL,
    )


def patch_profile(data: bytes) -> bytes:
    if PROFILE_POLICY in data:
        if data.count(PROFILE_POLICY) != 1:
            raise RuntimeError("profile-policy-duplicate")
        return data
    if data.count(PROFILE_ANCHOR) != 1:
        raise RuntimeError("profile-anchor-drift")
    return data.replace(PROFILE_ANCHOR, PROFILE_POLICY + PROFILE_ANCHOR, 1)


def setting(data: bytes, setting_id: str, value: str) -> bytes:
    pattern = re.compile(
        rb'(<setting id="' + re.escape(setting_id.encode()) + rb'"[^>]*>)([^<]*)(</setting>)'
    )
    matches = list(pattern.finditer(data))
    if len(matches) != 1:
        raise RuntimeError(f"setting-{setting_id}-count-{len(matches)}")
    return pattern.sub(lambda match: match.group(1) + value.encode() + match.group(3), data, count=1)


def update_settings(path: Path, *, transcode_all_hevc: bool) -> bool:
    original = path.read_bytes()
    desired = setting(original, "maxBitrate", MAX_BITRATE_INDEX)
    desired = setting(desired, "transcode_h265", "true" if transcode_all_hevc else "false")
    if desired == original:
        return False
    atomic_write(path, desired, path.stat().st_mode & 0o777)
    return True


def kodi_active(root: Path) -> bool:
    if root != Path("/"):
        return False
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", "kodi.service"], check=False
    )
    return result.returncode == 0


def write_json(path: Path, payload: dict) -> None:
    payload = dict(payload)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(path, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode(), 0o600)


def reconcile(root: Path = Path("/"), hostname: str | None = None) -> dict:
    hostname = hostname or socket.gethostname()
    if hostname != HOST:
        raise RuntimeError(f"host-refused:{hostname}")
    playutils, settings_path, state_path, status_path, _ = paths(root)
    current = playutils.read_bytes()
    current_hash = sha256(current)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    accepted_hash = state.get("accepted_patched_sha256")
    active = kodi_active(root)

    if accepted_hash and current_hash == accepted_hash and PROFILE_POLICY in current:
        update_settings(settings_path, transcode_all_hevc=False)
        outcome = {
            "mode": "selective",
            "reason": "accepted-patched-add-on",
            "playutils_sha256": current_hash,
            "max_bitrate_kbps": 18000,
            "hevc_direct_play_max_width": 1920,
        }
    elif current_hash == UPSTREAM_SHA256:
        patched = patch_profile(current)
        patched_hash = sha256(patched)
        atomic_write(playutils, patched, playutils.stat().st_mode & 0o777)
        write_json(
            state_path,
            {
                "schema": 1,
                "host": HOST,
                "upstream_sha256": UPSTREAM_SHA256,
                "accepted_patched_sha256": patched_hash,
            },
        )
        # If an update occurred while Kodi was running, its Python module may
        # remain cached.  Keep the supported all-HEVC fallback until reboot.
        update_settings(settings_path, transcode_all_hevc=active)
        outcome = {
            "mode": "fallback" if active else "selective",
            "reason": "known-add-on-patched-restart-required" if active else "known-add-on-patched",
            "playutils_sha256": patched_hash,
            "max_bitrate_kbps": 18000,
            "hevc_direct_play_max_width": None if active else 1920,
        }
    else:
        update_settings(settings_path, transcode_all_hevc=True)
        outcome = {
            "mode": "fallback",
            "reason": "unknown-add-on-hash",
            "playutils_sha256": current_hash,
            "max_bitrate_kbps": 18000,
            "hevc_direct_play_max_width": None,
            "review_required": True,
        }

    write_json(status_path, {"schema": 1, "host": HOST, **outcome})
    return outcome


def install(root: Path = Path("/"), hostname: str | None = None) -> dict:
    hostname = hostname or socket.gethostname()
    if hostname != HOST:
        raise RuntimeError(f"host-refused:{hostname}")
    if kodi_active(root):
        raise RuntimeError("kodi-must-be-stopped-for-install")
    playutils, settings_path, _, _, unit_dir = paths(root)
    if sha256(playutils.read_bytes()) != UPSTREAM_SHA256:
        raise RuntimeError("initial-playutils-hash-drift")

    storage = root / "storage" if root != Path("/") else Path("/storage")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    checkpoint = storage / ".aster-checkpoints" / f"astertv-jen-jellyfin-policy-{stamp}"
    checkpoint.mkdir(parents=True, exist_ok=False)
    shutil.copy2(playutils, checkpoint / "playutils.py")
    shutil.copy2(settings_path, checkpoint / "settings.xml")
    atomic_write(checkpoint / "SHA256SUMS", (
        f"{sha256(playutils.read_bytes())}  playutils.py\n"
        f"{sha256(settings_path.read_bytes())}  settings.xml\n"
    ).encode(), 0o600)

    policy_dir = storage / POLICY_DIR.relative_to("/storage")
    atomic_write(policy_dir / SCRIPT_NAME, Path(__file__).read_bytes(), 0o700)
    atomic_write(unit_dir / SERVICE_NAME, SERVICE.encode(), 0o644)
    atomic_write(unit_dir / PATH_NAME, PATH_UNIT.encode(), 0o644)
    outcome = reconcile(root, hostname)
    outcome["checkpoint"] = str(checkpoint)

    if root == Path("/"):
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", SERVICE_NAME, PATH_NAME], check=True)
        subprocess.run(["systemctl", "start", PATH_NAME], check=True)
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("install", "reconcile"))
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--hostname")
    args = parser.parse_args()
    result = install(args.root, args.hostname) if args.command == "install" else reconcile(args.root, args.hostname)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
