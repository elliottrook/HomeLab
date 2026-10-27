#!/usr/bin/env python3
"""Convert an unpacked, secret-free HP candidate into an Aster production payload."""

import hashlib
import json
import shutil
import sys
from pathlib import Path


SUPPORTED = ("AsterTV", "AsterTVProd")


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
    for name, row in family["components"].items():
        component = runtime / name
        manifest = component / "manifest.json"
        rows = refresh_file_rows(manifest, component)
        row["files"] = len(rows["files"])
        row["manifest_sha256"] = digest(manifest)

    music_manifest = runtime / "music72-manifest.json"
    music = refresh_file_rows(music_manifest, addons)
    music["boundary"] = "Aster clients only; explicit per-client normal profile; owned playback capped at 20000 queue items/200 per write; confirmed private create-only shared saves"
    write_json(music_manifest, music)
    family["music_manifest_sha256"] = digest(music_manifest)
    skin = addons / "skin.asterhome"
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
