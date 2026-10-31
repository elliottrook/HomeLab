#!/usr/bin/env python3
"""Build the immutable r35 recovery bundle from the accepted r27 release."""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[3]
DIST = ROOT / "services/kodi/dist"
SOURCE = DIST / "astertv-v2.0.7-production-2026-10-30-r27.tar.gz"
OUTPUT = DIST / "astertv-v2.0.7-production-2026-10-31-r35.tar.gz"
PREFIX = "aster-v2-package/"
OLD_RELEASE = "astertv-v2.0.7-production-2026-10-30-r27"
RELEASE = "astertv-v2.0.7-production-2026-10-31-r35"
EXPECTED_SETTINGS = "eb1a430b43d4c6a542952731af040fa51f0b497d3621208ef8e7470814687f43"
EXPECTED_DISPATCH = "fecf29c1d90fedb95535aa281c2f27317aa3309aebebcc236569a95f43061034"
EXPECTED_SAVER_SETTINGS = "b960e76f62a1db356b6c613409a34093553c5ea0d65cdb1720e825614c30d725"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def patch_settings(data: bytes) -> bytes:
    if sha(data) != EXPECTED_SETTINGS:
        raise RuntimeError("unexpected r27 SettingsCategory")
    text = data.decode()
    replacements = (
        ('<control type="button" id="10">\n            <width>',
         '<control type="button" id="10">\n            <onright>5</onright>\n            <width>'),
        ('<control type="radiobutton" id="20">\n            <left>',
         '<control type="radiobutton" id="20">\n            <onup>3</onup><onright>5</onright>\n            <left>'),
    )
    for old, new in replacements:
        if text.count(old) != 1:
            raise RuntimeError("Settings navigation source mismatch")
        text = text.replace(old, new, 1)
    for control_type, control_id in (("button", 7), ("radiobutton", 8),
                                     ("spincontrolex", 9), ("sliderex", 13),
                                     ("colorbutton", 15)):
        old = f'<control type="{control_type}" id="{control_id}">\n            <width>'
        new = (f'<control type="{control_type}" id="{control_id}">\n'
               '            <onleft>3</onleft>\n            <width>')
        if text.count(old) != 1:
            raise RuntimeError("Settings template source mismatch")
        text = text.replace(old, new, 1)
    return text.encode()


def patch_saver_settings(data: bytes) -> bytes:
    if sha(data) != EXPECTED_SAVER_SETTINGS or data.count(b'default="black"') != 1:
        raise RuntimeError("unexpected r27 screensaver settings")
    return data.replace(b'default="black"', b'default="aster"', 1)


def patch_promoter(data: bytes) -> bytes:
    text = data.decode().replace("production-r27-20261030", "production-r35-20261031")
    text = text.replace(OLD_RELEASE, RELEASE)
    text = text.replace(
        "AUDIO_SETTINGS = (\n",
        'CLOCK_SETTING = "locale.use24hourclock"\nAUDIO_SETTINGS = (\n', 1)
    anchor = "def addon_state(addon_id: str) -> bool | None:\n"
    clock = '''def set_24h_clock() -> None:
    result = kodi_rpc("Settings.SetSettingValue", {"setting": CLOCK_SETTING, "value": "24hours"})
    current = kodi_rpc("Settings.GetSettingValue", {"setting": CLOCK_SETTING})["value"]
    if result is not True or current != "24hours":
        raise RuntimeError("24-hour clock setting did not persist")


'''
    if text.count(anchor) != 1:
        raise RuntimeError("promoter clock anchor missing")
    text = text.replace(anchor, clock + anchor, 1)
    text = text.replace(
        "saved_audio = audio_settings()\n",
        'saved_audio = audio_settings()\n    saved_clock = kodi_rpc("Settings.GetSettingValue", {"setting": CLOCK_SETTING})["value"]\n', 1)
    text = text.replace(
        '"audio_settings_before": saved_audio,\n',
        '"audio_settings_before": saved_audio,\n        "clock_setting_before": saved_clock,\n', 1)
    text = text.replace(
        "restore_audio_settings(saved_audio)\n        activate_runtime_addons()\n",
        "restore_audio_settings(saved_audio)\n        set_24h_clock()\n        activate_runtime_addons()\n", 1)
    text = text.replace(
        "restore_audio_settings(saved_audio)\n            for addon_id, enabled in saved_addon_states.items():\n",
        'restore_audio_settings(saved_audio)\n            kodi_rpc("Settings.SetSettingValue", {"setting": CLOCK_SETTING, "value": saved_clock})\n            for addon_id, enabled in saved_addon_states.items():\n', 1)
    if OLD_RELEASE in text or "production-r27-20261030" in text:
        raise RuntimeError("promoter release replacement incomplete")
    compile(text, "promote_v207_to_production.py", "exec")
    return text.encode()


def main() -> None:
    with tarfile.open(SOURCE, "r:gz") as archive:
        members = {member.name: (copy.copy(member), archive.extractfile(member).read()
                   if member.isfile() else None) for member in archive.getmembers()}

    snapshot_root = PREFIX + "lab-addon-snapshot/"
    replacements = {
        "skin.asterhome/1080i/SettingsCategory.xml": patch_settings(
            members[snapshot_root + "skin.asterhome/1080i/SettingsCategory.xml"][1]),
        "skin.asterhome/tools/select_dispatch.py": (
            ROOT / "services/kodi/astertv-v2/reconciliation/payload/skin.asterhome/tools/select_dispatch.py"
        ).read_bytes(),
        "screensaver.asterhome.v2lab/resources/settings.xml": patch_saver_settings(
            members[snapshot_root + "screensaver.asterhome.v2lab/resources/settings.xml"][1]),
    }
    if sha(members[snapshot_root + "skin.asterhome/tools/select_dispatch.py"][1]) \
            != EXPECTED_DISPATCH:
        raise RuntimeError("unexpected r27 select dispatcher")
    compile(replacements["skin.asterhome/tools/select_dispatch.py"],
            "select_dispatch.py", "exec")
    for relative, data in replacements.items():
        name = snapshot_root + relative
        members[name] = (members[name][0], data)

    snapshot_name = PREFIX + "lab-addon-snapshot-manifest.json"
    snapshot = json.loads(members[snapshot_name][1])
    if snapshot.get("release") != OLD_RELEASE or len(snapshot.get("files", [])) != 577:
        raise RuntimeError("unexpected r27 snapshot")
    snapshot["release"] = RELEASE
    pending = set(replacements)
    for row in snapshot["files"]:
        if row["path"] in replacements:
            data = replacements[row["path"]]
            row["bytes"] = len(data)
            row["sha256"] = sha(data)
            pending.remove(row["path"])
    if pending:
        raise RuntimeError("snapshot replacements missing: " + repr(pending))
    snapshot_data = encoded(snapshot)
    members[snapshot_name] = (members[snapshot_name][0], snapshot_data)

    promoter_name = PREFIX + "reconciliation/promote_v207_to_production.py"
    promoter_data = patch_promoter(members[promoter_name][1])
    members[promoter_name] = (members[promoter_name][0], promoter_data)

    added = {}
    for relative in (
        "reconciliation/apply_production_settings_clock_r30_fix.py",
        "reconciliation/apply_production_settings_screensaver_r34_fix.py",
    ):
        data = (ROOT / "services/kodi/astertv-v2" / relative).read_bytes()
        compile(data, relative, "exec")
        name = PREFIX + relative
        info = copy.copy(members[promoter_name][0])
        info.name, info.mode, info.size = name, 0o755, len(data)
        members[name] = (info, data)
        added[relative] = data

    readme_name = PREFIX + "README.txt"
    heading = f"""# AsterTV v2.0.7 production recovery release r35 — 2026-10-31

r35 supersedes r27. It preserves every accepted r27 fix, pins Kodi's explicit
24-hour override during promotion, carries the repaired Settings category and
G20 OK paths, and makes the selected Aster screensaver display its moving mark
over an opaque black background. Kodi profile credentials and audio settings
remain outside the archive.

"""
    readme_data = (heading + members[readme_name][1].decode()).encode()
    members[readme_name] = (members[readme_name][0], readme_data)

    manifest_name = PREFIX + "manifest.json"
    manifest = json.loads(members[manifest_name][1])
    manifest["release"] = RELEASE
    manifest["source_commit"] = "8a323649+r35"
    manifest["artifacts"]["lab-addon-snapshot-manifest.json"] = sha(snapshot_data)
    manifest["artifacts"]["reconciliation/promote_v207_to_production.py"] = sha(promoter_data)
    for relative, data in added.items():
        manifest["artifacts"][relative] = sha(data)
    manifest["promotion_guards"].extend((
        "pin-and-verify-24-hour-clock-after-kodi-start",
        "restore-prior-clock-setting-on-rollback",
        "settings-category-focus-links-hash-pinned",
        "direct-g20-settings-dispatch-hash-pinned",
        "aster-screensaver-mark-default-hash-pinned",
    ))
    members[manifest_name] = (members[manifest_name][0], encoded(manifest))

    with OUTPUT.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for name in sorted(members):
                    info, data = members[name]
                    info.name = name
                    info.uid = info.gid = 0
                    info.uname = info.gname = "root"
                    info.mtime = 0
                    if data is None:
                        archive.addfile(info)
                    else:
                        info.size = len(data)
                        archive.addfile(info, io.BytesIO(data))
    digest = sha(OUTPUT.read_bytes())
    OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
        f"{digest}  {OUTPUT.name}\n")
    print(f"{OUTPUT} {digest}")


if __name__ == "__main__":
    main()
