"""Build the immutable HP TV-series responsiveness successor."""

import argparse
import json
from pathlib import Path
import shutil

import series_latency_followup as subject


TARGETS = {
    "default.py": ".kodi/addons/script.asterruntime/aster-series-preview24/default.py",
    "component-manifest.json": ".kodi/addons/script.asterruntime/aster-series-preview24/manifest.json",
    "aster_v2_series.py": ".kodi/addons/skin.asterhome/tools/aster_v2_series.py",
    "select_dispatch.py": ".kodi/addons/skin.asterhome/tools/select_dispatch.py",
    "family-manifest.json": ".kodi/addons/script.asterruntime/family-manifest.json",
}


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError("series-latency-output")
    raw = {name: (source / name).read_bytes() for name in TARGETS}
    runtime = subject.runtime(raw["default.py"], Path(__file__).parent / "series_preview/default.py")
    component = subject.component(raw["component-manifest.json"], runtime)
    launcher = subject.launcher(raw["aster_v2_series.py"], component)
    dispatcher = subject.dispatcher(raw["select_dispatch.py"])
    family = subject.family(raw["family-manifest.json"], component, launcher, dispatcher)
    changed = {"default.py": runtime, "component-manifest.json": component,
               "aster_v2_series.py": launcher, "select_dispatch.py": dispatcher,
               "family-manifest.json": family}
    output.mkdir(parents=True)
    rows = []
    for name, path in TARGETS.items():
        target = output / "payload" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(changed[name])
        rows.append({"path": path, "before_sha256": subject.PREDECESSORS[name],
                     "sha256": subject.sha(changed[name]), "bytes": len(changed[name])})
    helper = Path(__file__).parent / "tools/deploy_series_latency_followup.py"
    shutil.copyfile(helper, output / helper.name)
    manifest = {"schema": 1, "kind": "hp-series-latency-followup.v1",
                "production_changed": False, "files": rows,
                "helper_sha256": subject.sha(helper.read_bytes())}
    rendered = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(rendered)
    return subject.sha(rendered)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("source"); parser.add_argument("output")
    args = parser.parse_args(); print(build(args.source, args.output))
