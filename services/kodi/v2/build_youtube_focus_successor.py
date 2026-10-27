import argparse
import hashlib
import json
from pathlib import Path
import shutil

from youtube_focus_successor import PREDECESSOR, transform


TARGET = ".kodi/addons/skin.asterhome/1080i/MyVideoNav.xml"


def sha(raw): return hashlib.sha256(raw).hexdigest()


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists(): raise ValueError("youtube-focus-output")
    changed = transform(source.read_bytes())
    target = output / "payload" / TARGET
    target.parent.mkdir(parents=True); target.write_bytes(changed)
    helper = Path(__file__).with_name("tools") / "deploy_youtube_focus_successor.py"
    shutil.copyfile(helper, output / helper.name)
    value = {"schema": 1, "kind": "hp-youtube-focus-successor.v1",
             "file": {"path": TARGET, "before_sha256": PREDECESSOR,
                      "sha256": sha(changed)},
             "helper_sha256": sha(helper.read_bytes()),
             "production_changed": False}
    raw = json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(raw); return sha(raw)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("source"); p.add_argument("output")
    a = p.parse_args(); print(build(a.source, a.output))
