#!/usr/bin/env python3
"""Convert an unpacked, secret-free HP candidate into an Aster production payload."""

import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SUPPORTED = ("AsterTV", "AsterTVProd")
YOUTUBE_ROOT = "plugin://plugin.video.youtube/"
YOUTUBE_BACK_ACTION = (
    "RunScript(special://home/addons/skin.asterhome/tools/youtube_back.py)"
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace(path, old, new, count=1):
    path = Path(path)
    text = path.read_text()
    if text.count(old) != count:
        raise RuntimeError(f"unexpected-source:{path}:{text.count(old)}")
    path.write_text(text.replace(old, new))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def refresh_file_rows(manifest, base):
    data = json.loads(manifest.read_text())
    for row in data.get("files", []):
        path = base / row["path"]
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"missing-manifest-file:{path}")
        row["bytes"] = path.stat().st_size
        row["sha256"] = digest(path)
    write_json(manifest, data)
    return data


def rewrite_embedded_pin(path, old_pin, new_pin):
    """Retarget a launcher after production host edits change its component manifest."""
    path = Path(path)
    raw = path.read_bytes()
    old = old_pin.encode()
    new = new_pin.encode()
    if len(old_pin) != 64 or len(new_pin) != 64 or raw.count(old) != 1 or new in raw:
        raise RuntimeError(f"unexpected-embedded-pin:{path}")
    path.write_bytes(raw.replace(old, new, 1))


def adapt_youtube_entry_timing(path):
    """Wait for Kodi 22 to populate the official root before row focus."""
    path = Path(path)
    raw = path.read_bytes()
    old = b'AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:01,silent)'
    new = b'AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:03,silent)'
    if raw.count(old) != 1 or new in raw:
        raise RuntimeError('unexpected-youtube-entry-timing')
    path.write_bytes(raw.replace(old, new, 1))


def add_youtube_back_navigation(root):
    """Install a bounded Kodi 22 Back handler without a resident monitor."""
    root = Path(root)
    skin = root / ".kodi/addons/skin.asterhome"
    source = Path(__file__).resolve().parents[2] / "skin.asterhome/tools/youtube_back.py"
    target = skin / "tools/youtube_back.py"
    if not source.is_file():
        raise RuntimeError("unexpected-youtube-back-helper")
    if target.exists():
        if target.read_bytes() != source.read_bytes():
            raise RuntimeError("unexpected-youtube-back-helper")
    else:
        shutil.copy2(source, target)

    nav = skin / "1080i/MyVideoNav.xml"
    xml = ET.fromstring(nav.read_bytes())
    for identity in (9305, 9404):
        button = xml.find(f".//control[@id='{identity}']")
        action = button.find("onclick") if button is not None else None
        if action is None or action.text not in ("Action(Back)", YOUTUBE_BACK_ACTION):
            raise RuntimeError(f"unexpected-youtube-back-button:{identity}")
        action.text = YOUTUBE_BACK_ACTION
    nav.write_bytes(ET.tostring(xml, encoding="utf-8", xml_declaration=True))

    keymap = root / ".kodi/userdata/keymaps/g20s-pro-plus.xml"
    xml = ET.fromstring(keymap.read_bytes())
    window = xml.find("MyVideoNav")
    if window is None:
        window = ET.SubElement(xml, "MyVideoNav")
        keyboard = ET.SubElement(window, "keyboard")
        for name in ("escape", "backspace", "browser_back"):
            ET.SubElement(keyboard, name).text = YOUTUBE_BACK_ACTION
        mouse = ET.SubElement(window, "mouse")
        ET.SubElement(mouse, "rightclick").text = YOUTUBE_BACK_ACTION
    else:
        expected = ('./keyboard/escape', './keyboard/backspace',
                    './keyboard/browser_back', './mouse/rightclick')
        if (len(list(window.iter())) != 7 or
                any(window.findtext(name) != YOUTUBE_BACK_ACTION for name in expected)):
            raise RuntimeError("unexpected-youtube-keymap")
    keymap.write_bytes(ET.tostring(xml, encoding="utf-8", xml_declaration=True))
    return target


def build(root, host):
    root = Path(root).resolve()
    if host != "AsterTVProd" or not (root / ".kodi/addons/skin.asterhome").is_dir():
        raise RuntimeError("production-payload-boundary")
    addons = root / ".kodi/addons"

    patches = {
        "plugin.audio.asterbooks/service.py": [
            ("    if os.uname().nodename=='AsterTV' and flag.is_file() and not flag.is_symlink():\n"
             "        try:enabled=json.loads(flag.read_text())==dict(enabled=True,host='AsterTV',account_sha256=ACCOUNT,kind='aster-books-sync-pilot.v1')",
             "    host=os.uname().nodename\n"
             "    if host in ('AsterTV','AsterTVProd') and flag.is_file() and not flag.is_symlink():\n"
             "        try:enabled=json.loads(flag.read_text())==dict(enabled=True,host=host,account_sha256=ACCOUNT,kind='aster-books-sync-pilot.v1')"),
        ],
        "plugin.audio.asterbooks/resources/lib/books_sleep_ui.py": [
            ("if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')",
             "if os.uname().nodename not in ('AsterTV','AsterTVProd'):raise RuntimeError('aster-client-only')"),
        ],
        "screensaver.asterhome.v2lab/default.py": [
            ("if os.uname().nodename!='AsterTV' or not active():return",
             "if os.uname().nodename not in ('AsterTV','AsterTVProd') or not active():return"),
        ],
        "script.asteracquisition/default.py": [
            ('if os.uname().nodename != "AsterTV":',
             'if os.uname().nodename not in ("AsterTV", "AsterTVProd"):'),
        ],
        "script.astermusic.v2lab/default.py": [
            ("if platform.node()!='AsterTV' or (kind!='pilot' and not normal_playback()):",
             "if platform.node() not in ('AsterTV','AsterTVProd') or (kind!='pilot' and not normal_playback()):"),
            ("Normal Music integration is enabled only on the HP lab.",
             "Normal Music integration is not enabled on this Aster client."),
        ],
        "script.astermusic.v2lab/resources/lib/music_trial.py": [
            ("if host!='AsterTV':return False", "if host not in ('AsterTV','AsterTVProd'):return False"),
            ("value['queue_limit']==20000 and value['host']=='AsterTV'",
             "value['queue_limit']==20000 and value['host']==host"),
            ("if host!='AsterTV':return ()", "if host not in ('AsterTV','AsterTVProd'):return ()"),
        ],
        "script.astermusic.v2lab/resources/lib/music_expanded_trial.py": [
            ("if host!='AsterTV':return (),3", "if host not in ('AsterTV','AsterTVProd'):return (),3"),
        ],
        "script.astermusic.v2lab/resources/lib/music_jellyfin.py": [
            ("if platform.node()!='AsterTV':raise PlaylistUnavailable('hp-only-playlist-reader')",
             "if platform.node() not in ('AsterTV','AsterTVProd'):raise PlaylistUnavailable('aster-client-only-playlist-reader')"),
            ('self.authorization=\'MediaBrowser Client="Aster Music Lab", Device="AsterTV", Version="0.1.0", UserId=\'+json.dumps(self.user_id)+\', Token=\'+json.dumps(token)',
             'self.authorization=\'MediaBrowser Client="Aster Music", Device=\'+json.dumps(platform.node())+\', Version="2.0.0", UserId=\'+json.dumps(self.user_id)+\', Token=\'+json.dumps(token)'),
        ],
        "script.asterruntime/aster-network-preview6/default.py": [
            ("if os.uname().nodename!='AsterTV':return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):return"),
        ],
        "script.asterruntime/aster-global-search-ui22/default.py": [
            ("if os.uname().nodename!='AsterTV':return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):return"),
        ],
        "script.asterruntime/aster-global-search-ui22/movie.py": [
            ("if os.uname().nodename!='AsterTV':return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):return"),
        ],
        "script.asterruntime/aster-series-preview24/default.py": [
            ("if os.uname().nodename!='AsterTV':return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):return", 2),
        ],
        "script.asterruntime/aster-digest-player8/default.py": [
            ("if os.uname().nodename != 'AsterTV': return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'): return"),
        ],
        "script.asterruntime/aster-digest-player8/resources/lib/digest_preview_source.py": [
            ("if os.uname().nodename != 'AsterTV': return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'): return"),
        ],
        "script.asterruntime/aster-digest-reader6/default.py": [
            ("if os.uname().nodename != 'AsterTV': return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'): return"),
        ],
        "script.asterruntime/aster-video-scrub5/default.py": [
            ("if os.uname().nodename!='AsterTV':return", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):return"),
        ],
        "script.asterseerr/default.py": [
            ("if os.uname().nodename != 'AsterTV':", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):"),
        ],
        "script.astervoice.v2lab/default.py": [
            ("if os.uname().nodename != 'AsterTV':", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):"),
        ],
        "service.aster.playerui/service.py": [
            ("if os.uname().nodename != 'AsterTV':", "if os.uname().nodename not in ('AsterTV','AsterTVProd'):"),
        ],
        "skin.asterhome/tools/aster_v2_series.py": [
            ("if platform.node()!='AsterTV':return False", "if platform.node() not in ('AsterTV','AsterTVProd'):return False"),
        ],
        "skin.asterhome/tools/aster_v2_music.py": [
            ("if platform.node()!='AsterTV' or", "if platform.node() not in ('AsterTV','AsterTVProd') or"),
            ("platform.node()!='AsterTV':return", "platform.node() not in ('AsterTV','AsterTVProd'):return"),
        ],
        "skin.asterhome/tools/aster_v2_digest.py": [
            ("if os.uname().nodename != 'AsterTV' or", "if os.uname().nodename not in ('AsterTV','AsterTVProd') or"),
        ],
        "skin.asterhome/tools/osd_choices.py": [
            ("if os.uname().nodename!='AsterTV' or", "if os.uname().nodename not in ('AsterTV','AsterTVProd') or"),
        ],
        "skin.asterhome/tools/header_search.py": [
            ("require(os.uname().nodename=='AsterTV','hp-only')",
             "require(os.uname().nodename in ('AsterTV','AsterTVProd'),'aster-client-only')"),
        ],
    }
    for relative, edits in patches.items():
        for edit in edits:
            replace(addons / relative, *edit)

    reader_roots = (
        root / ".aster-staging/aster-books-compiler-reader-v1",
        root / ".aster-staging/aster-epub-consumer1/reader",
    )
    for reader in reader_roots:
        replace(reader / "default.py",
                'require(os.uname().nodename == "AsterTV" and len(sys.argv) == 3, "books-hp-only")',
                'require(os.uname().nodename in ("AsterTV", "AsterTVProd") and len(sys.argv) == 3, "books-client-only")')
        bundle_path = reader / "bundle.json"
        bundle = json.loads(bundle_path.read_text())
        bundle["files"]["default.py"] = digest(reader / "default.py")
        bundle["hp_only"] = False
        write_json(bundle_path, bundle)

    consumer = root / ".aster-staging/aster-epub-consumer1"
    consumer_manifest_path = consumer / "manifest.json"
    consumer_manifest = json.loads(consumer_manifest_path.read_text())
    for relative in ("reader/default.py", "reader/bundle.json"):
        consumer_manifest["files"][relative] = digest(consumer / relative)
    consumer_manifest["reader_pin"] = digest(consumer / "reader/bundle.json")
    consumer_manifest["hp_only"] = False
    write_json(consumer_manifest_path, consumer_manifest)

    activation_path = root / ".aster-state/aster-books-compiler-reader-v1/activation.json"
    activation = json.loads(activation_path.read_text())
    activation["bundle_sha256"] = digest(reader_roots[0] / "bundle.json")
    write_json(activation_path, activation)

    for profile, key in (("script.astermusic.v2lab", "normal-playback.json"),
                         ("plugin.audio.asterbooks", "progress-enabled.json")):
        path = root / ".kodi/userdata/addon_data" / profile / key
        if key == "progress-enabled.json" and not path.exists():
            continue  # Credential-bound profile state is transferred separately.
        data = json.loads(path.read_text())
        data["host"] = host
        write_json(path, data)
        path.chmod(0o600)

    runtime = addons / "script.asterruntime"
    family_path = runtime / "family-manifest.json"
    family = json.loads(family_path.read_text())
    predecessor_pins = {
        name: row["manifest_sha256"] for name, row in family["components"].items()
    }
    for name, row in family["components"].items():
        component = runtime / name
        manifest = component / "manifest.json"
        rows = refresh_file_rows(manifest, component)
        row["files"] = len(rows["files"])
        row["manifest_sha256"] = digest(manifest)

    # TV's launcher and Search handoff both pin the series component. Retarget
    # those consumers after the production host edit, then reseal Search.
    series_pin = family["components"]["aster-series-preview24"]["manifest_sha256"]
    rewrite_embedded_pin(
        addons / "skin.asterhome/tools/aster_v2_series.py",
        predecessor_pins["aster-series-preview24"], series_pin,
    )
    rewrite_embedded_pin(
        runtime / "aster-global-search-ui22/resources/lib/search_handoff.py",
        predecessor_pins["aster-series-preview24"], series_pin,
    )
    search = runtime / "aster-global-search-ui22"
    search_rows = refresh_file_rows(search / "manifest.json", search)
    family["components"]["aster-global-search-ui22"]["files"] = len(search_rows["files"])
    family["components"]["aster-global-search-ui22"]["manifest_sha256"] = digest(search / "manifest.json")

    # The family builder pins the Digest component from its skin launcher.
    # Production host admission edits change that component manifest, so the
    # launcher must follow the new installed pin before skin hashes are sealed.
    rewrite_embedded_pin(
        addons / "skin.asterhome/tools/aster_v2_digest.py",
        predecessor_pins["aster-digest-player8"],
        family["components"]["aster-digest-player8"]["manifest_sha256"],
    )
    adapt_youtube_entry_timing(addons / "skin.asterhome/1080i/MyVideoNav.xml")
    youtube_back = add_youtube_back_navigation(root)

    music_manifest = runtime / "music72-manifest.json"
    music = refresh_file_rows(music_manifest, addons)
    music["boundary"] = "Aster clients only; explicit per-client normal profile; owned playback capped at 20000 queue items/200 per write; confirmed private create-only shared saves"
    write_json(music_manifest, music)
    family["music_manifest_sha256"] = digest(music_manifest)
    skin = addons / "skin.asterhome"
    family["skin"]["tools/youtube_back.py"] = digest(youtube_back)
    for relative in tuple(family["skin"]):
        family["skin"][relative] = digest(skin / relative)
    write_json(family_path, family)

    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache)
    for name in ("aster-global-search-20261024", "aster-movie-playback-20261024",
                 "aster-series-playback-20261024", "aster-video-scrub-20261024",
                 "aster-voice-search1"):
        (root / ".aster-checkpoints" / name).mkdir(parents=True, exist_ok=True)

    forbidden = ("nodename!='AsterTV'", "nodename != 'AsterTV'", "nodename==\"AsterTV\"",
                 "nodename=='AsterTV'", "platform.node()!='AsterTV'")
    scan = [addons / name for name in patches]
    scan += [reader / "default.py" for reader in reader_roots]
    for path in scan:
        text = path.read_text()
        if any(value in text for value in forbidden):
            raise RuntimeError(f"remaining-lab-host-guard:{path}")
    return family_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_production_successor.py ROOT AsterTVProd")
    print(build(sys.argv[1], sys.argv[2]))
