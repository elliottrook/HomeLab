"""Isolated material replay for the AsterTV clean-recovery core chain."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

from recovery_bundle import verify
from release_inventory import require


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_tree(source: Path, target: Path) -> None:
    require(source.is_dir() and not source.is_symlink(), "rehearsal-source")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        require(not path.is_symlink(), "rehearsal-linked-source")
        if path.is_dir():
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def extract(archive: Path, target: Path, expected: list[dict]) -> None:
    expected_map = {row["path"]: row for row in expected}
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        require(len(names) == len(set(names)) == len(expected_map),
                "rehearsal-archive-members")
        for name in names:
            pure = PurePosixPath(name)
            require(not pure.is_absolute() and ".." not in pure.parts
                    and not name.endswith("/"), "rehearsal-archive-path")
            row = expected_map.get(name)
            require(row is not None, "rehearsal-archive-unexpected")
            raw = package.read(name)
            require(len(raw) == row["bytes"]
                    and hashlib.sha256(raw).hexdigest() == row["sha256"],
                    "rehearsal-archive-drift")
            destination = target / pure
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)


def run(bundle: Path, pin: str, output: Path, active_family_pin: str) -> dict:
    require(output.as_posix().startswith("/tmp/") and not output.exists(),
            "rehearsal-output")
    verify(bundle, pin)
    sources = bundle / "sources"
    base = sources / "aster-home-v1.1.1-candidate1"
    release = json.loads((base / "aster-home-v1.1.1-manifest.json").read_bytes())
    require(release.get("schema") == "aster-home-kodi-release.v1"
            and release.get("release") == "1.1.1", "rehearsal-base")
    addons = output / "storage/.kodi/addons"
    addons.mkdir(parents=True)
    try:
        for row in release["archives"]:
            archive = base / row["archive"]
            require(sha(archive) == row["sha256"]
                    and archive.stat().st_size == row["bytes"],
                    "rehearsal-base-archive")
            extract(archive, addons, row["files"])

        family = sources / "aster-family-recovery7b"
        copy_tree(family / "script.asterruntime", addons / "script.asterruntime")
        copy_tree(family / "skin", addons / "skin.asterhome")
        predecessor = family / "external/player.py.before"
        player = addons / "plugin.video.jellyfin/jellyfin_kodi/player.py"
        player.parent.mkdir(parents=True); shutil.copyfile(predecessor, player)
        shutil.copyfile(family / "external/player.py", player)

        music = sources / "aster-music-v2lab-0.1.0-candidate72"
        music_manifest = json.loads((music / "manifest.json").read_bytes())
        archive = music / "script.astermusic.v2lab-0.1.0.zip"
        require(sha(archive) == music_manifest["sha256"], "rehearsal-music-pin")
        extract(archive, addons, music_manifest["files"])

        doctor = sources / "aster-epub-doctor2-candidate"
        doctor_manifest = json.loads((doctor / "manifest.json").read_bytes())
        copy_tree(doctor / "payload/runtime", addons / "script.asterruntime")
        copy_tree(doctor / "payload/skin", addons / "skin.asterhome")

        active = addons / "script.asterruntime/family-manifest.json"
        require(sha(active) == active_family_pin
                == doctor_manifest["after"]["family_manifest"],
                "rehearsal-active-family")
        require(sha(addons / "skin.asterhome/1080i/Settings.xml")
                == doctor_manifest["after"]["settings"],
                "rehearsal-doctor-settings")
        recovery = json.loads((family / "manifest.json").read_bytes())
        require(sha(player) == recovery["external"][0]["sha256"],
                "rehearsal-jellyfin-guard")
        result = {"applied": True, "base_archives": len(release["archives"]),
                  "active_family_sha256": sha(active),
                  "music_package_sha256": sha(archive),
                  "jellyfin_guard_sha256": sha(player)}
    finally:
        if output.exists():
            shutil.rmtree(output)
    require(not output.exists(), "rehearsal-rollback")
    result["rolled_back"] = True
    return result
