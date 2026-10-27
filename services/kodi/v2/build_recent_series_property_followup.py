"""Build the immutable HP Recently Added property-route successor."""

import argparse
import json
from pathlib import Path
import shutil

import recent_series_property_followup as subject


TARGETS = {
    "plugin.py": ".kodi/addons/plugin.video.asterhome/default.py",
    "launcher.py": ".kodi/addons/skin.asterhome/tools/aster_v2_series.py",
    "family.json": ".kodi/addons/script.asterruntime/family-manifest.json",
}


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError("recent-property-output")
    raw = {name: (source / name).read_bytes() for name in TARGETS}
    plugin = subject.plugin(raw["plugin.py"])
    launcher = subject.launcher(raw["launcher.py"])
    family = subject.family(raw["family.json"], launcher)
    changed = {"plugin.py": plugin, "launcher.py": launcher, "family.json": family}
    output.mkdir(parents=True)
    rows = []
    for name, path in TARGETS.items():
        target = output / "payload" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(changed[name])
        rows.append({"path": path, "before_sha256": subject.PREDECESSORS[name],
                     "sha256": subject.sha(changed[name]), "bytes": len(changed[name])})
    helper = Path(__file__).parent / "tools/deploy_recent_series_property_followup.py"
    shutil.copyfile(helper, output / helper.name)
    manifest = {"schema": 1, "kind": "hp-recent-series-property.v1",
                "production_changed": False, "files": rows,
                "helper_sha256": subject.sha(helper.read_bytes())}
    rendered = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(rendered)
    return subject.sha(rendered)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("source"); parser.add_argument("output")
    args = parser.parse_args(); print(build(args.source, args.output))
