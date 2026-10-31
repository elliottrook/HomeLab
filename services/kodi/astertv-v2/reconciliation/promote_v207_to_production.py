#!/usr/bin/env python3
"""Promote the hash-pinned AsterTV v2.0.7 snapshot to AsterTVProd."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

PACKAGE = Path(__file__).resolve().parents[1]
SNAPSHOT = PACKAGE / "lab-addon-snapshot"
SNAPSHOT_MANIFEST = PACKAGE / "lab-addon-snapshot-manifest.json"
RECONCILIATION = PACKAGE / "reconciliation"
KEYMAP_SOURCE = RECONCILIATION / "payload/userdata/keymaps/g20s-pro-plus.xml"
SPLASH_SOURCE = PACKAGE / "profile-overlay/media/Splash.png"
ADDONS = Path("/storage/.kodi/addons")
KEYMAP = Path("/storage/.kodi/userdata/keymaps/g20s-pro-plus.xml")
SPLASH = Path("/storage/.kodi/media/Splash.png")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-production-r19-20261030")
RELEASE = "astertv-v2.0.7-production-2026-10-30-r19"
SPLASH_SHA = "912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce"
AUDIO_SETTINGS = (
    "audiooutput.audiodevice",
    "audiooutput.passthroughdevice",
    "audiooutput.passthrough",
    "audiooutput.channels",
    "audiooutput.config",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def kodi_rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        return json.loads(client.recv(65536).decode()).get("result")


def require_idle() -> None:
    if kodi_rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player or JSON-RPC error")


def audio_settings() -> dict:
    return {key: kodi_rpc("Settings.GetSettingValue", {"setting": key})["value"]
            for key in AUDIO_SETTINGS}


def restore_audio_settings(expected: dict) -> None:
    """Repair Kodi 22's bounded HDMI-startup fallback after the engine settles."""
    last = None
    for _ in range(15):
        for key in AUDIO_SETTINGS:
            kodi_rpc("Settings.SetSettingValue", {"setting": key, "value": expected[key]})
        time.sleep(2)
        last = audio_settings()
        if last == expected:
            return
    raise RuntimeError("audio settings did not survive post-start verification: " + repr(last))


def snapshot_rows() -> tuple[dict, list[dict]]:
    manifest = json.loads(SNAPSHOT_MANIFEST.read_text())
    if manifest.get("release") != RELEASE or manifest.get("credentials_included") is not False:
        raise RuntimeError("unexpected snapshot release or credential policy")
    rows = manifest.get("files")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("empty snapshot manifest")
    for row in rows:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts or "addon_data" in relative.parts:
            raise RuntimeError("unsafe snapshot path")
        source = SNAPSHOT / relative
        if not source.is_file() or source.stat().st_size != row["bytes"] or sha(source) != row["sha256"]:
            raise RuntimeError("snapshot mismatch: " + row["path"])
    return manifest, rows


def verify_installed(rows: list[dict]) -> None:
    for row in rows:
        target = ADDONS / row["path"]
        if not target.is_file() or target.stat().st_size != row["bytes"] or sha(target) != row["sha256"]:
            raise RuntimeError("installed snapshot mismatch: " + row["path"])


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    require_idle()
    saved_audio = audio_settings()
    manifest, rows = snapshot_rows()
    if sha(SPLASH_SOURCE) != SPLASH_SHA:
        raise RuntimeError("unexpected splash hash")
    if not KEYMAP_SOURCE.is_file():
        raise RuntimeError("release keymap missing")
    addon_names = sorted(path.name for path in SNAPSHOT.iterdir() if path.is_dir())
    if not addon_names:
        raise RuntimeError("snapshot addon set empty")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    old_addons = CHECKPOINT / "addons"
    old_addons.mkdir(mode=0o700)
    staged: dict[str, Path] = {}
    for name in addon_names:
        candidate = ADDONS / ("." + name + ".v207-new")
        if candidate.exists():
            raise RuntimeError("stale candidate: " + str(candidate))
        shutil.copytree(SNAPSHOT / name, candidate, symlinks=False)
        staged[name] = candidate

    metadata = {
        "release": RELEASE,
        "snapshot_manifest_sha256": sha(SNAPSHOT_MANIFEST),
        "addons": addon_names,
        "keymap_before": sha(KEYMAP) if KEYMAP.is_file() else None,
        "splash_before": sha(SPLASH) if SPLASH.is_file() else None,
        "credentials_or_addon_data_touched": False,
        "audio_settings_touched": False,
        "audio_settings_before": saved_audio,
    }
    (CHECKPOINT / "manifest.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    if KEYMAP.is_file():
        shutil.copy2(KEYMAP, CHECKPOINT / "g20s-pro-plus.xml.before")
    if SPLASH.is_file():
        shutil.copy2(SPLASH, CHECKPOINT / "Splash.png.before")

    moved_old: list[str] = []
    installed: list[str] = []
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=45)
    try:
        for name in addon_names:
            target = ADDONS / name
            if target.exists():
                os.replace(target, old_addons / name)
                moved_old.append(name)
            os.replace(staged[name], target)
            installed.append(name)
        KEYMAP.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        SPLASH.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        shutil.copy2(KEYMAP_SOURCE, KEYMAP)
        shutil.copy2(SPLASH_SOURCE, SPLASH)
        verify_installed(rows)
        if sha(SPLASH) != SPLASH_SHA:
            raise RuntimeError("installed splash mismatch")
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=45)
        time.sleep(8)
        if subprocess.run(["systemctl", "is-active", "--quiet", "kodi"]).returncode != 0:
            raise RuntimeError("Kodi did not remain active")
        restore_audio_settings(saved_audio)
        require_idle()
    except Exception:
        subprocess.run(["systemctl", "stop", "kodi"], check=False, timeout=45)
        failed = CHECKPOINT / "failed-v207"
        failed.mkdir(mode=0o700, exist_ok=True)
        for name in reversed(installed):
            target = ADDONS / name
            if target.exists():
                os.replace(target, failed / name)
            original = old_addons / name
            if original.exists():
                os.replace(original, target)
        if (CHECKPOINT / "g20s-pro-plus.xml.before").is_file():
            shutil.copy2(CHECKPOINT / "g20s-pro-plus.xml.before", KEYMAP)
        elif KEYMAP.exists():
            KEYMAP.unlink()
        if (CHECKPOINT / "Splash.png.before").is_file():
            shutil.copy2(CHECKPOINT / "Splash.png.before", SPLASH)
        elif SPLASH.exists():
            SPLASH.unlink()
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=45)
        time.sleep(8)
        try:
            restore_audio_settings(saved_audio)
        except Exception:
            Path("/storage/.aster-recovery-required").write_text(
                "AsterTV v2.0.7 rollback restored add-ons but not the pre-deployment audio route.\n")
        raise
    print(json.dumps({"installed": True, "release": RELEASE, "host": "AsterTVProd",
                      "checkpoint": str(CHECKPOINT), "addons": len(addon_names),
                      "snapshot_files": len(rows), "splash_sha256": SPLASH_SHA}, sort_keys=True))


if __name__ == "__main__":
    main()
