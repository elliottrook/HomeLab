"""Build the immutable HP owner-review correction candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from review_corrections import PREDECESSORS, family, home, includes, side_rail, youtube


TARGETS = {
    "Home.xml": ".kodi/addons/skin.asterhome/1080i/Home.xml",
    "MyVideoNav.xml": ".kodi/addons/skin.asterhome/1080i/MyVideoNav.xml",
    "Includes.xml": ".kodi/addons/skin.asterhome/1080i/Includes.xml",
    "IncludesHub.xml": ".kodi/addons/skin.asterhome/1080i/IncludesHub.xml",
    "custom_1112_home.xml": ".kodi/addons/skin.asterhome/1080i/custom_1112_home.xml",
    "Settings.xml": ".kodi/addons/skin.asterhome/1080i/Settings.xml",
    "custom_1111_digest.xml": ".kodi/addons/skin.asterhome/1080i/custom_1111_digest.xml",
    "IncludesBooks.xml": ".kodi/addons/skin.asterhome/1080i/IncludesBooks.xml",
    "custom_1122_breaking.xml": ".kodi/addons/skin.asterhome/1080i/custom_1122_breaking.xml",
    "IncludesMusic.xml": ".kodi/addons/skin.asterhome/1080i/IncludesMusic.xml",
    "family-manifest.json": ".kodi/addons/script.asterruntime/family-manifest.json",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(source: Path, output: Path) -> str:
    source, output = Path(source), Path(output)
    if output.exists(): raise ValueError("review-corrections-output")
    raw = {name: (source / name).read_bytes() for name in TARGETS}
    changed = {
        "Home.xml": home(raw["Home.xml"]),
        "MyVideoNav.xml": youtube(raw["MyVideoNav.xml"]),
        "Includes.xml": includes(raw["Includes.xml"]),
        "IncludesHub.xml": side_rail(raw["IncludesHub.xml"]),
    }
    for name in ("custom_1112_home.xml", "Settings.xml", "custom_1111_digest.xml",
                 "IncludesBooks.xml", "custom_1122_breaking.xml", "IncludesMusic.xml"):
        changed[name] = __import__("review_corrections").standard_search(raw[name], name)
    changed["family-manifest.json"] = family(raw["family-manifest.json"], changed)
    output.mkdir(parents=True)
    rows = []
    for name, target in TARGETS.items():
        destination = output / "payload" / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(changed[name])
        rows.append({"path": target, "before_sha256": PREDECESSORS[name],
                     "sha256": sha(changed[name]), "bytes": len(changed[name])})
    helper = Path(__file__).with_name("tools") / "deploy_review_corrections.py"
    shutil.copyfile(helper, output / helper.name)
    manifest = {"schema": 1, "kind": "hp-owner-review-corrections.v2",
                "production_changed": False, "files": rows,
                "helper_sha256": sha(helper.read_bytes())}
    rendered = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(rendered)
    return sha(rendered)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source"); parser.add_argument("output")
    args = parser.parse_args(); print(build(args.source, args.output))
