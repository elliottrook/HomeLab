#!/usr/bin/env python3
"""Build r46 from r35 with accepted Search, busy-logo and HDMI fixes."""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "services/kodi/astertv-v2"
DIST = ROOT / "services/kodi/dist"
SOURCE = DIST / "astertv-v2.0.7-production-2026-10-31-r35.tar.gz"
OUTPUT = DIST / "astertv-v2.0.7-production-2026-10-31-r46.tar.gz"
PREFIX = "aster-v2-package/"
OLD_RELEASE = "astertv-v2.0.7-production-2026-10-31-r35"
RELEASE = "astertv-v2.0.7-production-2026-10-31-r46"

sys.path.insert(0, str(HERE / "reconciliation"))
import apply_production_search_details_r42_fix as r42
import apply_production_movie_return_r43_fix as r43


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def patch_promoter(data: bytes) -> bytes:
    text = data.decode()
    text = text.replace("production-r35-20261031", "production-r46-20261031")
    text = text.replace(OLD_RELEASE, RELEASE)
    text = text.replace("import os\n", "import os\nimport re\nimport tempfile\n", 1)
    old_audio = '''AUDIO_SETTINGS = (
    "audiooutput.audiodevice",
    "audiooutput.passthroughdevice",
    "audiooutput.passthrough",
    "audiooutput.channels",
    "audiooutput.config",
)
'''
    new_audio = '''AUDIO_SETTINGS = (
    "audiooutput.audiodevice",
    "audiooutput.passthroughdevice",
    "audiooutput.passthrough",
    "audiooutput.channels",
    "audiooutput.config",
    "audiooutput.ac3passthrough",
    "audiooutput.eac3passthrough",
    "audiooutput.truehdpassthrough",
    "audiooutput.dtspassthrough",
    "audiooutput.dtshdpassthrough",
    "videoplayer.usedisplayasclock",
)
HDMI_ROUTE = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"
RELEASE_AUDIO = {
    "audiooutput.audiodevice": HDMI_ROUTE,
    "audiooutput.passthroughdevice": HDMI_ROUTE,
    "audiooutput.passthrough": True,
    "audiooutput.channels": 1,
    "audiooutput.config": 2,
    "audiooutput.ac3passthrough": True,
    "audiooutput.eac3passthrough": True,
    "audiooutput.truehdpassthrough": True,
    "audiooutput.dtspassthrough": False,
    "audiooutput.dtshdpassthrough": False,
    "videoplayer.usedisplayasclock": False,
}
GUISETTINGS = Path("/storage/.kodi/userdata/guisettings.xml")
PULSE = "pulseaudio.service"
'''
    if text.count(old_audio) != 1:
        raise RuntimeError("promoter audio settings anchor missing")
    text = text.replace(old_audio, new_audio, 1)
    anchor = "def set_24h_clock() -> None:\n"
    helpers = '''def atomic_profile_write(data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r46-", dir=GUISETTINGS.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.chmod(temporary, 0o600);os.replace(temporary, GUISETTINGS)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def pin_release_audio_file() -> None:
    text = GUISETTINGS.read_text()
    for setting in ("audiooutput.audiodevice", "audiooutput.passthroughdevice"):
        pattern = r'(<setting id="' + re.escape(setting) + r'">)[^<]*(</setting>)'
        text, count = re.subn(pattern, r"\\g<1>" + HDMI_ROUTE + r"\\g<2>", text, count=1)
        if count != 1:raise RuntimeError("missing profile audio route: " + setting)
    atomic_profile_write(text.encode())


def unit_state(verb: str) -> str:
    return subprocess.run(["systemctl", verb, PULSE], text=True,
                          capture_output=True, check=False).stdout.strip()


def configure_exclusive_hdmi() -> None:
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
    if text.count(anchor) != 1:
        raise RuntimeError("promoter helper anchor missing")
    text = text.replace(anchor, helpers + anchor, 1)
    text = text.replace(
        "saved_audio = audio_settings()\n",
        'saved_audio = audio_settings()\n    saved_pulse_enabled = unit_state("is-enabled")\n    saved_pulse_active = unit_state("is-active")\n', 1)
    text = text.replace(
        '"audio_settings_touched": False,\n',
        '"audio_settings_touched": True,\n        "release_audio_settings": RELEASE_AUDIO,\n        "pulseaudio_enabled_before": saved_pulse_enabled,\n        "pulseaudio_active_before": saved_pulse_active,\n', 1)
    text = text.replace(
        'shutil.copy2(SPLASH, CHECKPOINT / "Splash.png.before")\n',
        'shutil.copy2(SPLASH, CHECKPOINT / "Splash.png.before")\n    shutil.copy2(GUISETTINGS, CHECKPOINT / "guisettings.xml.before")\n', 1)
    text = text.replace(
        "subprocess.run([\"systemctl\", \"stop\", \"kodi\"], check=True, timeout=45)\n    try:\n",
        'subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=45)\n    try:\n        configure_exclusive_hdmi()\n', 1)
    text = text.replace(
        "restore_audio_settings(saved_audio)\n        set_24h_clock()\n",
        "restore_audio_settings(RELEASE_AUDIO)\n        set_24h_clock()\n", 1)
    rollback_anchor = '''        elif SPLASH.exists():
            SPLASH.unlink()
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=45)
'''
    rollback_new = '''        elif SPLASH.exists():
            SPLASH.unlink()
        shutil.copy2(CHECKPOINT / "guisettings.xml.before", GUISETTINGS)
        restore_pulse_state(saved_pulse_enabled, saved_pulse_active)
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=45)
'''
    if text.count(rollback_anchor) != 1:
        raise RuntimeError("promoter rollback anchor missing")
    text = text.replace(rollback_anchor, rollback_new, 1)
    if OLD_RELEASE in text or "production-r35-20261031" in text:
        raise RuntimeError("promoter release replacement incomplete")
    compile(text, "promote_v207_to_production.py", "exec")
    return text.encode()


def main() -> None:
    with tarfile.open(SOURCE, "r:gz") as archive:
        members = {member.name: (copy.copy(member), archive.extractfile(member).read()
                   if member.isfile() else None) for member in archive.getmembers()}

    snapshot_root = PREFIX + "lab-addon-snapshot/"
    get = lambda path: members[snapshot_root + path][1]
    default, search_manifest, family = r42.patched(
        get("script.asterruntime/aster-global-search-ui22/default.py"),
        get("script.asterruntime/aster-global-search-ui22/manifest.json"),
        get("script.asterruntime/family-manifest.json"))
    movie, search_manifest, family = r43.patched(
        get("script.asterruntime/aster-global-search-ui22/movie.py"),
        search_manifest, family)
    family_value = json.loads(family)

    dispatcher = (HERE / "reconciliation/payload/skin.asterhome/tools/select_dispatch.py").read_bytes()
    busy = (HERE / "reconciliation/payload/skin.asterhome/1080i/DialogBusy.xml").read_bytes()
    compile(dispatcher, "select_dispatch.py", "exec")
    family_value["skin"]["tools/select_dispatch.py"] = sha(dispatcher)
    family_value["skin"]["1080i/DialogBusy.xml"] = sha(busy)
    family = encoded(family_value)

    replacements = {
        "skin.asterhome/tools/select_dispatch.py": dispatcher,
        "skin.asterhome/1080i/DialogBusy.xml": busy,
        "script.asterruntime/aster-global-search-ui22/default.py": default,
        "script.asterruntime/aster-global-search-ui22/movie.py": movie,
        "script.asterruntime/aster-global-search-ui22/manifest.json": search_manifest,
        "script.asterruntime/family-manifest.json": family,
    }
    for relative, data in replacements.items():
        name = snapshot_root + relative
        members[name] = (members[name][0], data)

    snapshot_name = PREFIX + "lab-addon-snapshot-manifest.json"
    snapshot = json.loads(members[snapshot_name][1])
    if snapshot.get("release") != OLD_RELEASE or len(snapshot.get("files", [])) != 577:
        raise RuntimeError("unexpected r35 snapshot")
    snapshot["release"] = RELEASE
    pending = set(replacements)
    for row in snapshot["files"]:
        if row["path"] in replacements:
            data = replacements[row["path"]]
            row["bytes"] = len(data);row["sha256"] = sha(data)
            pending.remove(row["path"])
    if pending:
        raise RuntimeError("snapshot replacements missing: " + repr(pending))
    snapshot_data = encoded(snapshot)
    members[snapshot_name] = (members[snapshot_name][0], snapshot_data)

    promoter_name = PREFIX + "reconciliation/promote_v207_to_production.py"
    promoter_data = patch_promoter(members[promoter_name][1])
    members[promoter_name] = (members[promoter_name][0], promoter_data)

    added = {}
    additions = (
        "apply_production_busy_logo_r36_fix.py",
        "apply_production_passthrough_route_r37.py",
        "apply_production_dolby_r39_signal_trial.py",
        "apply_production_search_dispatch_r40_fix.py",
        "apply_production_search_manifest_r41_fix.py",
        "apply_production_search_details_r42_fix.py",
        "apply_production_movie_return_r43_fix.py",
        "apply_production_alsa_exclusive_r44_trial.py",
        "apply_production_alsa_exclusive_r45_trial.py",
    )
    template = members[promoter_name][0]
    for filename in additions:
        relative = "reconciliation/" + filename
        data = (HERE / relative).read_bytes();compile(data, relative, "exec")
        name = PREFIX + relative;info = copy.copy(template)
        info.name, info.mode, info.size = name, 0o755, len(data)
        members[name] = (info, data);added[relative] = data

    readme_name = PREFIX + "README.txt"
    heading = f"""# AsterTV v2.0.7 production release r46 — 2026-10-31

r46 supersedes r35. It preserves all accepted UI, Books, Music, TV, Requests,
YouTube, Home, Settings and screensaver fixes; adds the static Aster busy mark;
repairs Search entry, movie details and post-playback return; and pins exclusive
ALSA HDMI 0 with AC-3/E-AC-3/TrueHD passthrough. Production acceptance confirmed
E-AC-3 raw bitstream and HDR10 signalling end-to-end. Credentials remain outside
the archive.

"""
    members[readme_name] = (members[readme_name][0],
                            (heading + members[readme_name][1].decode()).encode())

    manifest_name = PREFIX + "manifest.json"
    manifest = json.loads(members[manifest_name][1])
    manifest["release"] = RELEASE
    manifest["source_commit"] = "8667ab6b+r46"
    manifest["audio_configuration_included"] = True
    manifest["artifacts"]["lab-addon-snapshot-manifest.json"] = sha(snapshot_data)
    manifest["artifacts"]["reconciliation/promote_v207_to_production.py"] = sha(promoter_data)
    for relative, data in added.items():manifest["artifacts"][relative] = sha(data)
    manifest["promotion_guards"].extend((
        "aster-busy-logo-hash-pinned",
        "search-dispatch-and-runtime-integrity-chain-hash-pinned",
        "movie-details-return-to-search-hash-pinned",
        "exclusive-alsa-hdmi-zero-before-kodi-start",
        "disable-pulseaudio-with-rollback-state-restore",
        "verified-eac3-truehd-capability-and-hdr10-production-acceptance",
    ))
    members[manifest_name] = (members[manifest_name][0], encoded(manifest))

    with OUTPUT.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for name in sorted(members):
                    info, data = members[name];info.name = name
                    info.uid = info.gid = 0;info.uname = info.gname = "root";info.mtime = 0
                    if data is None:archive.addfile(info)
                    else:
                        info.size = len(data);archive.addfile(info, io.BytesIO(data))
    digest = sha(OUTPUT.read_bytes())
    OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
        f"{digest}  {OUTPUT.name}\n")
    print(f"{OUTPUT} {digest}")


if __name__ == "__main__":
    main()
