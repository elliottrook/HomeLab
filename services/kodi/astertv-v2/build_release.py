#!/usr/bin/env python3
"""Build the final dual-target AsterTV v2.0.7 release from accepted r49."""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "services/kodi/astertv-v2"
DIST = ROOT / "services/kodi/dist"
SOURCE = DIST / "astertv-v2.0.7-production-2026-10-31-r49.tar.gz"
OUTPUT = DIST / "astertv-v2.0.7-release-2026-10-31.tar.gz"
PREFIX = "aster-v2-package/"
OLD_RELEASE = "astertv-v2.0.7-production-2026-10-31-r49"
RELEASE = "astertv-v2.0.7-release-2026-10-31"

HOST_PATHS = (
    "plugin.audio.asterbooks/resources/lib/books_sleep_ui.py",
    "plugin.audio.asterbooks/service.py",
    "script.asteracquisition/default.py",
    "script.asterbootstrap/default.py",
    "script.astermusic.v2lab/default.py",
    "script.astermusic.v2lab/resources/lib/music_expanded_trial.py",
    "script.astermusic.v2lab/resources/lib/music_jellyfin.py",
    "script.astermusic.v2lab/resources/lib/music_trial.py",
    "script.asterruntime/aster-digest-player8/default.py",
    "script.asterruntime/aster-digest-player8/resources/lib/digest_preview_source.py",
    "script.asterruntime/aster-digest-reader6/default.py",
    "script.asterruntime/aster-global-search-ui22/default.py",
    "script.asterruntime/aster-global-search-ui22/movie.py",
    "script.asterruntime/aster-network-preview6/default.py",
    "script.asterruntime/aster-series-preview24/default.py",
    "script.asterruntime/aster-video-scrub5/default.py",
    "script.asterseerr/default.py",
    "script.astervoice.v2lab/default.py",
    "service.aster.playerui/service.py",
    "skin.asterhome/tools/aster_v2_digest.py",
    "skin.asterhome/tools/aster_v2_music.py",
    "skin.asterhome/tools/aster_v2_series.py",
    "skin.asterhome/tools/header_search.py",
    "skin.asterhome/tools/osd_choices.py",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def renamed_hosts(data: bytes) -> bytes:
    text = data.decode()
    for old, new in (
        ("'AsterTVProd'", "'AsterTV-Family'"),
        ('"AsterTVProd"', '"AsterTV-Family"'),
        ("'AsterTV'", "'AsterTV-Bedroom'"),
        ('"AsterTV"', '"AsterTV-Bedroom"'),
    ):
        text = text.replace(old, new)
    if "'AsterTV'" in text or '"AsterTV"' in text or "AsterTVProd" in text:
        raise RuntimeError("incomplete hostname replacement")
    compile(text, "renamed-host-runtime.py", "exec")
    return text.encode()


def patch_promoter(data: bytes) -> bytes:
    text = data.decode()
    text = text.replace(
        '"""Promote the hash-pinned AsterTV v2.0.7 snapshot to AsterTVProd."""',
        '"""Install the final AsterTV v2.0.7 release on Family or Bedroom."""',
    )
    text = text.replace(OLD_RELEASE, RELEASE)
    old_audio_helpers = '''def audio_settings() -> dict:
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
'''
    new_audio_helpers = '''def audio_settings(required: tuple[str, ...] | None = None) -> dict:
    """Return supported audio settings; require an exact set when requested."""
    values = {}
    for key in required or AUDIO_SETTINGS:
        result = kodi_rpc("Settings.GetSettingValue", {"setting": key})
        if isinstance(result, dict) and "value" in result:
            values[key] = result["value"]
        elif required is not None:
            raise RuntimeError("required audio setting unavailable: " + key)
    return values


def restore_audio_settings(expected: dict) -> None:
    """Repair Kodi 22's bounded HDMI-startup fallback after the engine settles."""
    last = None
    keys = tuple(expected)
    for _ in range(15):
        for key, value in expected.items():
            kodi_rpc("Settings.SetSettingValue", {"setting": key, "value": value})
        time.sleep(2)
        last = audio_settings(keys)
        if last == expected:
            return
    raise RuntimeError("audio settings did not survive post-start verification: " + repr(last))
'''
    if text.count(old_audio_helpers) != 1:
        raise RuntimeError("promoter audio helper anchor missing")
    text = text.replace(old_audio_helpers, new_audio_helpers, 1)
    old_pulse_helpers = '''def configure_exclusive_hdmi() -> None:
    subprocess.run(["systemctl", "stop", PULSE], check=True, timeout=30)
    subprocess.run(["systemctl", "disable", PULSE], check=True, timeout=30)
    if unit_state("is-active") == "active":raise RuntimeError("PulseAudio remained active")
    pin_release_audio_file()


def restore_pulse_state(enabled: str, active: str) -> None:
    subprocess.run(["systemctl", "enable" if enabled == "enabled" else "disable", PULSE],
                   check=True, timeout=30)
    subprocess.run(["systemctl", "start" if active == "active" else "stop", PULSE],
                   check=True, timeout=30)
'''
    new_pulse_helpers = '''def configure_exclusive_hdmi() -> None:
    subprocess.run(["systemctl", "stop", PULSE], check=True, timeout=30)
    subprocess.run(["systemctl", "disable", PULSE], check=True, timeout=30)
    subprocess.run(["systemctl", "mask", PULSE], check=True, timeout=30)
    if unit_state("is-active") == "active":raise RuntimeError("PulseAudio remained active")
    if unit_state("is-enabled") != "masked":raise RuntimeError("PulseAudio mask did not persist")
    pin_release_audio_file()


def restore_pulse_state(enabled: str, active: str) -> None:
    subprocess.run(["systemctl", "unmask", PULSE], check=False, timeout=30)
    if enabled == "masked":
        subprocess.run(["systemctl", "mask", PULSE], check=True, timeout=30)
    else:
        subprocess.run(["systemctl", "enable" if enabled == "enabled" else "disable", PULSE],
                       check=True, timeout=30)
        subprocess.run(["systemctl", "start" if active == "active" else "stop", PULSE],
                       check=True, timeout=30)
'''
    if text.count(old_pulse_helpers) != 1:
        raise RuntimeError("promoter PulseAudio helper anchor missing")
    text = text.replace(old_pulse_helpers, new_pulse_helpers, 1)
    text = text.replace(
        'CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-production-r49-20261031")',
        "CHECKPOINT = None",
    )
    host_anchor = 'LAB_ONLY_ADDONS = ("script.asterbootstrap",)\n'
    host_block = '''LAB_ONLY_ADDONS = ("script.asterbootstrap",)\nTARGETS = {\n    "AsterTVProd": ("family", True),\n    "AsterTV-Family": ("family", True),\n    "AsterTV": ("bedroom", False),\n    "AsterTV-Bedroom": ("bedroom", False),\n}\n'''
    if text.count(host_anchor) != 1:
        raise RuntimeError("promoter host anchor missing")
    text = text.replace(host_anchor, host_block, 1)
    main_anchor = '''def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
'''
    main_new = '''def main() -> None:
    global CHECKPOINT
    node = os.uname().nodename
    if node not in TARGETS:
        raise RuntimeError("AsterTV Family/Bedroom host only")
    role, family_audio = TARGETS[node]
    CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-release-20261031-" + role)
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
'''
    if text.count(main_anchor) != 1:
        raise RuntimeError("promoter main anchor missing")
    text = text.replace(main_anchor, main_new, 1)
    text = text.replace(
        "    saved_audio = audio_settings()\n",
        "    saved_audio = audio_settings()\n    expected_audio = RELEASE_AUDIO if family_audio else saved_audio\n",
        1,
    )
    text = text.replace(
        '        "release_audio_settings": RELEASE_AUDIO,\n',
        '        "target_role": role,\n        "release_audio_settings": expected_audio,\n',
        1,
    )
    text = text.replace(
        "    try:\n        configure_exclusive_hdmi()\n",
        "    try:\n        if family_audio:\n            configure_exclusive_hdmi()\n",
        1,
    )
    text = text.replace(
        "        restore_audio_settings(RELEASE_AUDIO)\n",
        "        restore_audio_settings(expected_audio)\n",
        1,
    )
    old_print = '''    print(json.dumps({"installed": True, "release": RELEASE, "host": "AsterTVProd",
                      "checkpoint": str(CHECKPOINT), "addons": len(addon_names),
'''
    new_print = '''    print(json.dumps({"installed": True, "release": RELEASE, "host": node,
                      "target_role": role, "checkpoint": str(CHECKPOINT), "addons": len(addon_names),
'''
    if text.count(old_print) != 1:
        raise RuntimeError("promoter result anchor missing")
    text = text.replace(old_print, new_print, 1)
    if OLD_RELEASE in text:
        raise RuntimeError("promoter release replacement incomplete")
    compile(text, "promote_v207_to_production.py", "exec")
    return text.encode()


def main() -> None:
    with tarfile.open(SOURCE, "r:gz") as archive:
        members = {
            member.name: (
                copy.copy(member),
                archive.extractfile(member).read() if member.isfile() else None,
            )
            for member in archive.getmembers()
        }

    snapshot_root = PREFIX + "lab-addon-snapshot/"
    replacements: dict[str, bytes] = {}
    for relative in HOST_PATHS:
        replacements[relative] = renamed_hosts(members[snapshot_root + relative][1])

    payload = HERE / "reconciliation/payload/screensaver.asterhome.v2lab"
    for relative in (
        "screensaver.asterhome.v2lab/addon.xml",
        "screensaver.asterhome.v2lab/default.py",
        "screensaver.asterhome.v2lab/resources/skins/Default/1080i/AsterIdle.xml",
    ):
        replacements[relative] = (payload / relative.split("/", 1)[1]).read_bytes()

    # Reconcile component manifests for changed script.asterruntime members.
    component_manifests: dict[str, dict] = {}
    for relative, data in list(replacements.items()):
        parts = Path(relative).parts
        if len(parts) < 3 or parts[0] != "script.asterruntime" or parts[1] == "family-manifest.json":
            continue
        component = parts[1]
        manifest_relative = f"script.asterruntime/{component}/manifest.json"
        manifest = component_manifests.setdefault(
            component,
            json.loads(members[snapshot_root + manifest_relative][1]),
        )
        row_path = "/".join(parts[2:])
        rows = [row for row in manifest["files"] if row["path"] == row_path]
        if len(rows) != 1:
            raise RuntimeError("component manifest row missing: " + relative)
        rows[0]["bytes"], rows[0]["sha256"] = len(data), sha(data)
    for component, manifest in component_manifests.items():
        replacements[f"script.asterruntime/{component}/manifest.json"] = encoded(manifest)

    # Reconcile Music's separate manifest.
    music_relative = "script.asterruntime/music72-manifest.json"
    music = json.loads(members[snapshot_root + music_relative][1])
    for relative, data in replacements.items():
        if not relative.startswith("script.astermusic.v2lab/"):
            continue
        rows = [row for row in music["files"] if row["path"] == relative]
        if len(rows) != 1:
            raise RuntimeError("music manifest row missing: " + relative)
        rows[0]["bytes"], rows[0]["sha256"] = len(data), sha(data)
    replacements[music_relative] = encoded(music)

    # Reconcile the family manifest last.
    family_relative = "script.asterruntime/family-manifest.json"
    family = json.loads(members[snapshot_root + family_relative][1])
    for relative, data in replacements.items():
        if relative.startswith("skin.asterhome/"):
            key = relative.split("/", 1)[1]
            if key in family["skin"]:
                family["skin"][key] = sha(data)
    for component in component_manifests:
        manifest_relative = f"script.asterruntime/{component}/manifest.json"
        family["components"][component]["manifest_sha256"] = sha(replacements[manifest_relative])
    family["music_manifest_sha256"] = sha(replacements[music_relative])
    replacements[family_relative] = encoded(family)

    for relative, data in replacements.items():
        members[snapshot_root + relative] = (members[snapshot_root + relative][0], data)

    snapshot_name = PREFIX + "lab-addon-snapshot-manifest.json"
    snapshot = json.loads(members[snapshot_name][1])
    if snapshot["release"] != OLD_RELEASE or len(snapshot["files"]) != 577:
        raise RuntimeError("unexpected r49 snapshot")
    snapshot["release"] = RELEASE
    pending = set(replacements)
    for row in snapshot["files"]:
        if row["path"] in replacements:
            data = replacements[row["path"]]
            row["bytes"], row["sha256"] = len(data), sha(data)
            pending.remove(row["path"])
    if pending:
        raise RuntimeError("snapshot replacements missing: " + repr(pending))
    snapshot_data = encoded(snapshot)
    members[snapshot_name] = (members[snapshot_name][0], snapshot_data)

    promoter_name = PREFIX + "reconciliation/promote_v207_to_production.py"
    promoter_data = patch_promoter(members[promoter_name][1])
    members[promoter_name] = (members[promoter_name][0], promoter_data)

    test_relative = "reconciliation/test_production_media_screensaver_r50.py"
    test = (HERE / test_relative).read_bytes()
    compile(test, Path(test_relative).name, "exec")
    test_name = PREFIX + test_relative
    info = copy.copy(members[promoter_name][0])
    info.name, info.mode, info.size = test_name, 0o755, len(test)
    members[test_name] = (info, test)

    wish_relative = "ASTER-TV-V3-WISHLIST.md"
    wish = (ROOT / "services/kodi" / wish_relative).read_bytes()
    wish_name = PREFIX + wish_relative
    info = copy.copy(members[PREFIX + "README.txt"][0])
    info.name, info.mode, info.size = wish_name, 0o644, len(wish)
    members[wish_name] = (info, wish)

    readme_name = PREFIX + "README.txt"
    heading = f"""# AsterTV v2.0.7 final release — 2026-10-31

This final v2 release supersedes r49. It preserves every accepted UI, playback,
Dolby/HDR, Books, Music, News, Requests, Home and navigation repair; adds the
balanced four-library media-art screensaver; and adopts the client identities
AsterTV Family and AsterTV Bedroom. One target-aware promoter preserves Bedroom
audio while applying the accepted passthrough profile only to Family.

"""
    members[readme_name] = (
        members[readme_name][0],
        (heading + members[readme_name][1].decode()).encode(),
    )

    manifest_name = PREFIX + "manifest.json"
    manifest = json.loads(members[manifest_name][1])
    manifest["release"] = RELEASE
    manifest["status"] = "release"
    manifest["source_commit"] = "8c1f4a3a+release"
    manifest["lab_source"] = "AsterTV Bedroom (192.168.1.140)"
    manifest["production_target"] = "AsterTV Family (192.168.1.157)"
    manifest["artifacts"]["lab-addon-snapshot-manifest.json"] = sha(snapshot_data)
    manifest["artifacts"]["reconciliation/promote_v207_to_production.py"] = sha(promoter_data)
    manifest["artifacts"][test_relative] = sha(test)
    manifest["artifacts"][wish_relative] = sha(wish)
    manifest["promotion_guards"].extend((
        "family-bedroom-target-aware-audio",
        "runtime-host-identities-renamed-and-integrity-resealed",
        "balanced-four-library-media-screensaver",
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
        f"{digest}  {OUTPUT.name}\n"
    )
    print(f"{OUTPUT} {digest}")


if __name__ == "__main__":
    main()
