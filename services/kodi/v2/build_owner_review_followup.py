"""Build the immutable HP owner-review follow-up candidate."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import owner_review_followup as subject


TARGETS = {
    "Home.xml": ".kodi/addons/skin.asterhome/1080i/Home.xml",
    "MyVideoNav.xml": ".kodi/addons/skin.asterhome/1080i/MyVideoNav.xml",
    "IncludesHub.xml": ".kodi/addons/skin.asterhome/1080i/IncludesHub.xml",
    "IncludesBooks.xml": ".kodi/addons/skin.asterhome/1080i/IncludesBooks.xml",
    "IncludesMusic.xml": ".kodi/addons/skin.asterhome/1080i/IncludesMusic.xml",
    "Settings.xml": ".kodi/addons/skin.asterhome/1080i/Settings.xml",
    "custom_1133_acquisition.xml": ".kodi/addons/skin.asterhome/1080i/custom_1133_acquisition.xml",
    "family-manifest.json": ".kodi/addons/script.asterruntime/family-manifest.json",
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def build(source: Path, output: Path) -> str:
    source, output = Path(source), Path(output)
    if output.exists(): raise ValueError("owner-followup-output")
    raw = {name: (source / name).read_bytes() for name in TARGETS}
    changed = {
        "Home.xml": subject.home(raw["Home.xml"]),
        "MyVideoNav.xml": subject.media_browser(raw["MyVideoNav.xml"]),
        "IncludesHub.xml": subject.side_rail(raw["IncludesHub.xml"]),
        "IncludesBooks.xml": subject.books(raw["IncludesBooks.xml"]),
        "IncludesMusic.xml": subject.music(raw["IncludesMusic.xml"]),
        "Settings.xml": subject.settings(raw["Settings.xml"]),
        "custom_1133_acquisition.xml": subject.acquisition(raw["custom_1133_acquisition.xml"]),
    }
    changed["family-manifest.json"] = subject.family(raw["family-manifest.json"], changed)
    output.mkdir(parents=True); rows = []
    for name, path in TARGETS.items():
        target = output / "payload" / path; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(changed[name])
        rows.append({"path": path, "before_sha256": subject.PREDECESSORS[name],
                     "sha256": sha(changed[name]), "bytes": len(changed[name])})
    helper = Path(__file__).with_name("tools") / "deploy_owner_review_followup.py"
    shutil.copyfile(helper, output / helper.name)
    manifest = {"schema": 1, "kind": "hp-owner-review-followup.v1",
                "production_changed": False, "files": rows,
                "helper_sha256": sha(helper.read_bytes())}
    rendered = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(rendered)
    return sha(rendered)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("source"); parser.add_argument("output")
    args = parser.parse_args(); print(build(args.source, args.output))
