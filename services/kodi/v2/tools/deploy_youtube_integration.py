"""Install or recover the HP-only Aster presentation for official YouTube."""

import json
import os
from pathlib import Path
import shutil
import sys
import time

import xbmc
import xbmcgui

sys.path.insert(0, str(Path(__file__).parent))
import deploy_startup as guard


BASE = Path("/storage/.aster-staging/aster-youtube-integration3")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-youtube-integration3")
SKIN = Path("/storage/.kodi/addons/skin.asterhome/1080i")
MANIFEST = "f3657fdce7b95284719180db653b12dc7b92729e268b221a15784160d675b6c0"
TARGETS = ("Includes.xml", "MyVideoNav.xml")
require = guard.require


def exact(paths, expected):
    require(set(paths) == set(expected), "exact-target-set")
    for name, digest in expected.items():
        require(guard.sha(paths[name]) == digest, "file-drift-" + name)


def main(mode):
    require(os.uname().nodename == "AsterTV", "hp-only-no-production")
    require(mode in ("deploy", "verify", "rollback", "reinstall"), "mode")
    require(guard.idle(), "idle-empty-required")
    require(xbmcgui.getCurrentWindowId() == 10000, "home-window-required")
    require(guard.sha(BASE / "manifest.json") == MANIFEST, "pinned-manifest")
    manifest = json.loads((BASE / "manifest.json").read_text())
    require(tuple(manifest["targets"]) == TARGETS, "bounded-two-files")
    stage = {name: BASE / name for name in TARGETS}
    live = {name: SKIN / name for name in TARGETS}
    exact(stage, manifest["files"])

    if mode in ("deploy", "reinstall"):
        exact(live, manifest["predecessors"])
        before = guard.snapshot()
        if mode == "deploy":
            require(not CHECKPOINT.exists(), "checkpoint-already-exists")
            CHECKPOINT.mkdir(mode=0o700, parents=True)
            for name in TARGETS:
                shutil.copyfile(live[name], CHECKPOINT / (name + ".before"))
            (CHECKPOINT / "before.json").write_text(json.dumps(before, indent=2))
            shutil.copyfile(BASE / "manifest.json", CHECKPOINT / "manifest.json")
            shutil.copyfile(__file__, CHECKPOINT / "deploy_youtube_integration.py")
        else:
            require((CHECKPOINT / "rolled-back.json").exists(), "rollback-proof-required")
            require(before == json.loads((CHECKPOINT / "before.json").read_text()),
                    "settings-navigation-drift-after-rollback")
        exact({name: CHECKPOINT / (name + ".before") for name in TARGETS},
              manifest["predecessors"])
        require(guard.idle(), "playback-started-no-change")
        for name in TARGETS:
            temporary = live[name].with_suffix(".aster-tmp")
            shutil.copyfile(stage[name], temporary)
            os.replace(temporary, live[name])
        exact(live, manifest["files"])
        require(guard.snapshot() == before, "settings-navigation-drift")
        (CHECKPOINT / "installed.json").write_text(json.dumps({
            "ok": True, "manifest_sha256": MANIFEST,
            "official_addon": "plugin.video.youtube", "secret_files": 0,
        }, indent=2))
        if mode == "reinstall":
            (CHECKPOINT / "rolled-back.json").rename(
                CHECKPOINT / "rollback-rehearsal-passed.json")
        xbmc.executebuiltin("ReloadSkin")
        return {"ok": True, "mode": mode, "manifest_sha256": MANIFEST,
                "official_addon": True, "secret_files": 0}

    exact(live, manifest["files"])
    exact({name: CHECKPOINT / (name + ".before") for name in TARGETS},
          manifest["predecessors"])
    if mode == "verify":
        return {"ok": True, "mode": mode, "manifest_sha256": MANIFEST,
                "official_addon": True, "secret_files": 0}

    require(not (CHECKPOINT / "rolled-back.json").exists(), "rollback-already-used")
    for name in TARGETS:
        temporary = live[name].with_suffix(".aster-tmp")
        shutil.copyfile(CHECKPOINT / (name + ".before"), temporary)
        os.replace(temporary, live[name])
    exact(live, manifest["predecessors"])
    (CHECKPOINT / "rolled-back.json").write_text(json.dumps({
        "ok": True, "manifest_sha256": MANIFEST,
    }, indent=2))
    xbmc.executebuiltin("ReloadSkin")
    return {"ok": True, "mode": mode, "restored": list(TARGETS)}


if __name__ == "__main__":
    try:
        result = main(sys.argv[1] if len(sys.argv) == 2 else "verify")
    except Exception as error:
        result = {"ok": False, "code": str(error)}
    (BASE / ("result-" + str(time.time_ns()) + ".json")).write_text(
        json.dumps(result, indent=2))

