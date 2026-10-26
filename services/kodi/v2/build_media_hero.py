"""Build the immutable HP Media Recently Added/recommendation-hero stage."""

import argparse
import hashlib
import json
from pathlib import Path

from media_hero_home import (transform, update_family_manifest,
                             update_search_manifest)


HERE = Path(__file__).resolve().parent
STAGE = "aster-media-hero9"
TARGETS = {
    "plugin/default.py": "/storage/.kodi/addons/plugin.video.asterhome/default.py",
    "plugin/library.py": "/storage/.kodi/addons/plugin.video.asterhome/library.py",
    "skin/1080i/Home.xml": "/storage/.kodi/addons/skin.asterhome/1080i/Home.xml",
    "skin/1080i/Includes.xml": "/storage/.kodi/addons/skin.asterhome/1080i/Includes.xml",
    "skin/1080i/custom_1127_search.xml": "/storage/.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml",
    "runtime/custom_1127_search.xml": "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/overlay/custom_1127_search.xml",
    "runtime/search-manifest.json": "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/manifest.json",
    "runtime/family-manifest.json": "/storage/.kodi/addons/script.asterruntime/family-manifest.json",
}
PREDECESSORS = {
    "plugin/default.py": "50c5ecb4d676bdff544d47cfadd8f984a5f79b7d57a2af42682dbc3c7012dfb2",
    "plugin/library.py": "088c8acb4d5050e7cfe89db7d6bab3a5be9534b1f8b68663d6fb822c8bd08d99",
    "skin/1080i/Home.xml": "39b10fcac446626d3decd89e22cd8dda95b5ee50f9b5de489cb5f67f579a0834",
    "skin/1080i/Includes.xml": "fa1eb7f7c52e5e78a83d63ec19719b7fae9ce953cffdfbd89366cc625a9860fa",
    "skin/1080i/custom_1127_search.xml": "c7f85dc09859db9b4bf7aa3b971564e696e45c021b1880dc4c72913e202b043d",
    "runtime/custom_1127_search.xml": "6f1fbe60d9d1ef9187ad0524602268145c9412c5d2c886c104243103b692e55e",
    "runtime/search-manifest.json": "bc4b0938ad96a6e0c5f89a991389edc1d46f9b927f2f87735981ad4b483309ca",
    "runtime/family-manifest.json": "de5a22f20d6f4be2da5cdde22a7eb0159bb284feb33b315d8b9080518c8424c0",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("immutable-media-hero-stage")
    output.mkdir(parents=True)
    home = transform((HERE / "baselines/aster-family-recovery7b-Home.xml").read_bytes())
    search = (HERE / "search_native/overlay/custom_1127_search.xml").read_bytes()
    search_manifest = update_search_manifest(
        (HERE / "baselines/aster-global-search-ui22-manifest.json").read_bytes(),
        search)
    family_manifest = update_family_manifest(
        (HERE / "baselines/aster-family-runtime-manifest.json").read_bytes(),
        home, search, search_manifest)
    payloads = {
        "plugin/default.py": (HERE.parent / "plugin.video.asterhome/default.py").read_bytes(),
        "plugin/library.py": (HERE.parent / "plugin.video.asterhome/library.py").read_bytes(),
        "skin/1080i/Home.xml": home,
        "skin/1080i/Includes.xml": (HERE.parent / "skin.asterhome/1080i/Includes.xml").read_bytes(),
        "skin/1080i/custom_1127_search.xml": search,
        "runtime/custom_1127_search.xml": search,
        "runtime/search-manifest.json": search_manifest,
        "runtime/family-manifest.json": family_manifest,
    }
    rows = []
    for name, raw in payloads.items():
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        rows.append({"path": name, "target": TARGETS[name],
                     "sha256": digest(destination),
                     "previous_sha256": PREDECESSORS[name]})
    manifest = {"schema": 1, "kind": "hp-media-recommendation-hero",
                "stage": STAGE, "files": rows}
    raw = (json.dumps(manifest, indent=2) + "\n").encode()
    (output / "manifest.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    print(build(args.output))
