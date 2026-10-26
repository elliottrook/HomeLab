"""Build the immutable HP Media Recently Added/recommendation-hero stage."""

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
STAGE = "aster-media-hero3"
SOURCES = {
    "plugin/default.py": HERE.parent / "plugin.video.asterhome/default.py",
    "plugin/library.py": HERE.parent / "plugin.video.asterhome/library.py",
    "skin/1080i/Home.xml": HERE.parent / "skin.asterhome/1080i/Home.xml",
    "skin/1080i/Includes.xml": HERE.parent / "skin.asterhome/1080i/Includes.xml",
}
TARGETS = {
    "plugin/default.py": "/storage/.kodi/addons/plugin.video.asterhome/default.py",
    "plugin/library.py": "/storage/.kodi/addons/plugin.video.asterhome/library.py",
    "skin/1080i/Home.xml": "/storage/.kodi/addons/skin.asterhome/1080i/Home.xml",
    "skin/1080i/Includes.xml": "/storage/.kodi/addons/skin.asterhome/1080i/Includes.xml",
}
PREDECESSORS = {
    "plugin/default.py": "0b0a04f7555f8a3e7edc01e4632fd7ce7ccff8dcb5c94da8af5e905e9c8ef657",
    "plugin/library.py": "7964f719ad86ff18564ad2e849464ee151172b40654d9567b86bad35e1f56e69",
    "skin/1080i/Home.xml": "a5e785b9390543c2e103d0a06ece2de445c458fcc4649b7c699de83c5dc63f75",
    "skin/1080i/Includes.xml": "fa1eb7f7c52e5e78a83d63ec19719b7fae9ce953cffdfbd89366cc625a9860fa",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("immutable-media-hero-stage")
    output.mkdir(parents=True)
    rows = []
    for name, source in SOURCES.items():
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
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
