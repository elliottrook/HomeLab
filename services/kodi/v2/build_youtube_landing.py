"""Build the immutable HP-only Aster YouTube landing candidate."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from youtube_landing import extend_includes, extend_navigation, INCLUDES_SHA, NAV_SHA


HERE = Path(__file__).resolve().parent
TARGETS = {
    "1080i/Includes.xml": ".kodi/addons/skin.asterhome/1080i/Includes.xml",
    "1080i/MyVideoNav.xml": ".kodi/addons/skin.asterhome/1080i/MyVideoNav.xml",
}
PREDECESSORS = {
    TARGETS["1080i/Includes.xml"]:
        "f7a045f562918159607164106f3613c35ed787adb1a8913a542e9692970241d8",
    TARGETS["1080i/MyVideoNav.xml"]:
        "c5bfb3da5ef44a1fd21658ff3ebfd58e13e5973474dbdbff6d6774f10753bff5",
}


def sha(value):
    raw = value if isinstance(value, bytes) else Path(value).read_bytes()
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("immutable-youtube-landing-output")
    source = HERE.parent / "skin.asterhome/1080i"
    payloads = {
        TARGETS["1080i/Includes.xml"]:
            extend_includes((source / "Includes.xml").read_bytes()),
        TARGETS["1080i/MyVideoNav.xml"]:
            extend_navigation((source / "MyVideoNav.xml").read_bytes()),
    }
    output.mkdir(parents=True)
    rows = []
    for name, raw in sorted(payloads.items()):
        ET.fromstring(raw)
        destination = output / "payload" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        rows.append({"path": name, "bytes": len(raw), "sha256": sha(raw),
                     "before_sha256": PREDECESSORS[name]})
    helpers = {
        "youtube_landing_install.py": HERE / "youtube_landing_install.py",
        "deploy_youtube_landing.py": HERE / "tools/deploy_youtube_landing.py",
        "digest_news_install.py": HERE / "digest_news_install.py",
    }
    manifest = {
        "schema": 1,
        "kind": "hp-aster-youtube-landing.v2",
        "official_addon": "plugin.video.youtube",
        "files": rows,
        "helpers": {},
        "routes": ["aster-search", "subscriptions", "recommendations",
                   "watch-later", "channels"],
        "rows": ["subscriptions", "recommendations", "watch-later"],
        "search_view": ["aster-keyboard", "focused-result-hero",
                        "multi-row-result-grid"],
        "credential_files": 0,
        "production_changed": False,
    }
    for name, source_path in helpers.items():
        raw = source_path.read_bytes()
        (output / name).write_bytes(raw)
        manifest["helpers"][name] = sha(raw)
    raw = encoded(manifest)
    (output / "manifest.json").write_bytes(raw)
    return sha(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    arguments = parser.parse_args()
    print(build(arguments.output))
