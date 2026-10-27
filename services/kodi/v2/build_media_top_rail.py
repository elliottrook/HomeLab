"""Build the immutable HP Media top-rail correction."""

import argparse
import hashlib
import json
from pathlib import Path

from media_top_rail import ACCEPTED_HOME, transform


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(home, output):
    home, output = Path(home), Path(output)
    if output.exists() or home.is_symlink() or not home.is_file():
        raise ValueError("media-top-rail-build-path")
    raw = home.read_bytes()
    if sha(raw) != ACCEPTED_HOME:
        raise ValueError("media-top-rail-build-predecessor")
    output.mkdir(parents=True)
    payload = output / "payload/.kodi/addons/skin.asterhome/1080i/Home.xml"
    payload.parent.mkdir(parents=True)
    successor = transform(raw); payload.write_bytes(successor)
    here = Path(__file__).resolve().parent
    helper = (here / "media_top_rail_install.py").read_bytes()
    (output / "media_top_rail_install.py").write_bytes(helper)
    deploy = (here / "tools/deploy_media_top_rail.py").read_bytes()
    (output / "deploy_media_top_rail.py").write_bytes(deploy)
    manifest = {
        "schema": 1, "kind": "hp-media-top-rail.v2",
        "parent_manifest_sha256":
            "3edb117155442a8d9a035478c019fd6eaf9ae2ad63971bac7d09c2905d8b8930",
        "file": {"path": ".kodi/addons/skin.asterhome/1080i/Home.xml",
                 "bytes": len(successor), "sha256": sha(successor),
                 "before_sha256": ACCEPTED_HOME},
        "helper_sha256": sha(helper), "deploy_sha256": sha(deploy),
    }
    encoded = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(encoded)
    return sha(encoded)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(build(args.home, args.output))
