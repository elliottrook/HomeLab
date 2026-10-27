"""Build an immutable, discovery-only Aster Acquisition Hub candidate."""

import argparse
import hashlib
import json
from pathlib import Path

from acquisition_home_launcher import add_hub


ADDON = "script.asteracquisition"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"


def build(home, output):
    home, output = Path(home), Path(output)
    if output.exists() or not home.is_file() or home.is_symlink():
        raise ValueError("acquisition-build-path")
    output.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    addon = output / ADDON
    sources = {
        "default.py": here / "acquisition_native/default.py",
        "resources/lib/acquisition_hub_model.py": here / "acquisition_hub_model.py",
        "resources/lib/acquisition_page_model.py": here / "acquisition_page_model.py",
        "resources/lib/discovery_feed_client.py": here / "discovery_feed_client.py",
        "resources/lib/landing_recommendations.py": here / "landing_recommendations.py",
    }
    for relative, source in sources.items():
        if not source.is_file() or source.is_symlink():
            raise ValueError("acquisition-build-source")
        target = addon / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    (addon / "addon.xml").write_bytes(b'''<?xml version="1.0" encoding="UTF-8"?>
<addon id="script.asteracquisition" name="Aster Acquisition Hub" version="2.0.0" provider-name="Aster Home">
  <requires><import addon="xbmc.python" version="3.0.0"/></requires>
  <extension point="xbmc.python.script" library="default.py"><provides>executable</provides></extension>
  <extension point="xbmc.addon.metadata"><summary lang="en_GB">Private cross-media discovery page</summary><description lang="en_GB">Credential-free Aster discovery for Media, Music and Books.</description><platform>all</platform><license>Private HomeLab</license></extension>
</addon>
''')
    original = home.read_bytes()
    transformed = add_hub(original.decode("utf-8")).encode()
    overlay = (here / "acquisition_native/overlay/custom_1133_acquisition.xml").read_bytes()
    skin_files = {
        "1080i/Home.xml": (transformed, digest(original)),
        "1080i/custom_1133_acquisition.xml": (overlay, None),
    }
    skin_rows = []
    for relative, (raw, before) in skin_files.items():
        target = output / "skin" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        skin_rows.append({"path": relative, "bytes": len(raw),
                          "sha256": digest(raw), "before_sha256": before})
    addon_rows = []
    for path in sorted(addon.rglob("*")):
        if path.is_file():
            raw = path.read_bytes()
            addon_rows.append({"path": path.relative_to(addon).as_posix(),
                               "bytes": len(raw), "sha256": digest(raw)})
    helper = here / "acquisition_install.py"
    helper_raw = helper.read_bytes()
    (output / "acquisition_install.py").write_bytes(helper_raw)
    manifest = {
        "schema": 1,
        "kind": "hp-acquisition-page.v1",
        "addon": ADDON,
        "addon_files": addon_rows,
        "skin": skin_rows,
        "helpers": {"acquisition_install.py": digest(helper_raw)},
        "activation": "RunScript(script.asteracquisition)",
        "writes_enabled": False,
    }
    (output / "manifest.json").write_bytes(encoded(manifest))
    return digest((output / "manifest.json").read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(build(args.home, args.output))
