"""Build the immutable Acquisition Hub primary-action repair."""

import hashlib
import json
from pathlib import Path


PARENT = "2cb7e1319b6521f3043d832ed5a4969f249adaede591f60fb968334e6092c3b4"
FILES = {
    ".kodi/addons/script.asteracquisition/default.py": (
        "acquisition_native/default.py",
        "01897d9ad327e432bc55683da05b92e7648220e4f8f56fb7fa77747c18cfdafd",
    ),
    ".kodi/addons/skin.asterhome/1080i/custom_1133_acquisition.xml": (
        "acquisition_native/overlay/custom_1133_acquisition.xml",
        "39b0a95bd15f2d34f9d1be6fadbb178d11466a599ddf634e1377214171f41224",
    ),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("acquisition-label-output-exists")
    output.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    rows = []
    for target, (source, before) in FILES.items():
        raw = (here / source).read_bytes()
        path = output / "payload" / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        rows.append({"path": target, "bytes": len(raw), "sha256": sha(raw),
                     "before_sha256": before})
    helper = (here / "acquisition_label_patch_install.py").read_bytes()
    (output / "acquisition_label_patch_install.py").write_bytes(helper)
    manifest = {"schema": 1, "kind": "hp-acquisition-label-patch.v2",
                "parent_manifest_sha256": PARENT, "files": rows,
                "helper_sha256": sha(helper)}
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(raw)
    return sha(raw)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    print(build(parser.parse_args().output))
