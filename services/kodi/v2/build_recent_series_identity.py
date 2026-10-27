"""Build the immutable HP Recently Added series-identity patch."""

import argparse
import json
from pathlib import Path
import shutil

import recent_series_identity as subject


TARGET = ".kodi/addons/plugin.video.asterhome/default.py"


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError("recent-series-output")
    raw = (source / "default.py").read_bytes()
    candidate = subject.render(raw)
    target = output / "payload" / TARGET
    target.parent.mkdir(parents=True)
    target.write_bytes(candidate)
    helper = Path(__file__).parent / "tools/deploy_recent_series_identity.py"
    shutil.copyfile(helper, output / helper.name)
    manifest = {
        "schema": 1,
        "kind": "hp-recent-series-identity.v1",
        "production_changed": False,
        "files": [{
            "path": TARGET,
            "before_sha256": subject.PREDECESSOR,
            "sha256": subject.sha(candidate),
            "bytes": len(candidate),
        }],
        "helper_sha256": subject.sha(helper.read_bytes()),
    }
    rendered = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(rendered)
    return subject.sha(rendered)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    print(build(args.source, args.output))
