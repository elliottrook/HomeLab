"""Rehearse non-secret AsterTV service/add-on recovery in a disposable root."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import wave
import zipfile

from recovery_bundle import verify
from release_inventory import require


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_files(root: Path, rows: dict[str, str]) -> None:
    for relative, wanted in rows.items():
        path = root / relative
        require(path.is_file() and not path.is_symlink()
                and sha(path) == wanted, "late-stage-file")


def copy_files(root: Path, rows: dict[str, str], target: Path) -> None:
    verified_files(root, rows)
    for relative in sorted(rows):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)


def extract(archive: Path, target: Path, rows: list[dict], prefix: str = "") -> None:
    expected = {row["path"]: row for row in rows}
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        require(len(names) == len(set(names)) == len(expected),
                "late-stage-archive-members")
        for name in names:
            pure = PurePosixPath(name)
            require(not pure.is_absolute() and ".." not in pure.parts
                    and not name.endswith("/") and name.startswith(prefix),
                    "late-stage-archive-path")
            relative = name[len(prefix):]
            require(relative in expected and relative, "late-stage-archive-path")
            raw = package.read(name); row = expected[relative]
            require(len(raw) == row["bytes"]
                    and hashlib.sha256(raw).hexdigest() == row["sha256"],
                    "late-stage-archive-drift")
            destination = target / PurePosixPath(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)


def check_mount_units(stage: Path, rows: dict[str, str]) -> None:
    names = set(rows)
    expected = {
        "storage-aster\\x2dreader-generations.automount",
        "storage-aster\\x2dreader-generations.mount",
        "storage-aster\\x2dreader-ready.automount",
        "storage-aster\\x2dreader-ready.mount",
    }
    require(names == expected, "late-stage-units")
    for leaf in ("generations", "ready"):
        mount = (stage / ("storage-aster\\x2dreader-" + leaf + ".mount")).read_text()
        automount = (stage / ("storage-aster\\x2dreader-" + leaf + ".automount")).read_text()
        require("What=192.168.20.40:/mnt/Media/AsterReader/" + leaf in mount
                and "Where=/storage/aster-reader/" + leaf in mount
                and "Options=ro,nosuid,nodev,noexec," in mount
                and "_netdev" in mount and "Type=nfs" in mount,
                "late-stage-mount-policy")
        require("Where=/storage/aster-reader/" + leaf in automount
                and "TimeoutIdleSec=300" in automount,
                "late-stage-automount-policy")


def run(bundle: Path, pin: str, output: Path) -> dict:
    require(output.as_posix().startswith("/tmp/") and not output.exists(),
            "late-stage-output")
    verify(bundle, pin)
    sources = bundle / "sources"
    output.mkdir(parents=True)
    try:
        books = sources / "aster-books-compiler-reader-v1"
        book_manifest = json.loads((books / "bundle.json").read_bytes())
        require(book_manifest.get("kind") == "aster-books-compiler-reader-v1"
                and book_manifest.get("compiler_commit") == "fc91fcd4",
                "late-stage-books-contract")
        copy_files(books, book_manifest["files"],
                   output / "storage/.kodi/addons/script.asterbooks.compiler")

        consumer = sources / "aster-epub-consumer1"
        consumer_manifest = json.loads((consumer / "manifest.json").read_bytes())
        require(consumer_manifest.get("kind") == "aster-hp-compiled-epub-consumer-v1"
                and consumer_manifest.get("hp_only") is True,
                "late-stage-consumer-contract")
        verified_files(consumer, consumer_manifest["files"])
        require(sha(consumer / "reader/bundle.json")
                == consumer_manifest["reader_pin"], "late-stage-reader-pin")
        check_mount_units(consumer / "units", consumer_manifest["unit_sha256"])
        copy_files(consumer / "units", consumer_manifest["unit_sha256"],
                   output / "storage/.config/system.d")
        books_target = output / "storage/.kodi/addons/skin.asterhome/tools/books_data.py"
        books_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(consumer / "books_data.py", books_target)

        camera = sources / "aster-camera2"
        camera_manifest = json.loads((camera / "manifest.json").read_bytes())
        require(camera_manifest.get("kind") == "hp-one-camera-v1"
                and set(camera_manifest["files"]) == {
                    "aster-camera.service", "camera-idle.png", "custom_1112_home.xml",
                    "frame.py", "proxy.py", "view.py"}, "late-stage-camera-contract")
        verified_files(camera, camera_manifest["files"])
        unit = (camera / "aster-camera.service").read_text()
        proxy = (camera / "proxy.py").read_text()
        require("NoNewPrivileges=true" in unit and "ProtectSystem=strict" in unit
                and "MemoryMax=96M" in unit and "CPUQuota=25%" in unit,
                "late-stage-camera-sandbox")
        require("Server(('127.0.0.1',15102),Handler)" in proxy
                and "self.client_address[0]=='127.0.0.1'" in proxy,
                "late-stage-camera-loopback")
        copy_files(camera, {name: camera_manifest["files"][name]
                            for name in ("proxy.py", "view.py", "camera-idle.png")},
                   output / "storage/.aster-camera")
        camera_unit = output / "storage/.config/system.d/aster-camera.service"
        camera_unit.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(camera / "aster-camera.service", camera_unit)

        sounds = sources / "aster-canonical-sounds-20261025/resources"
        names = {path.name for path in sounds.iterdir() if path.is_file()}
        require(names == {"back.wav", "nav-down.wav", "nav-left.wav", "nav-right.wav",
                          "nav-up.wav", "notify.wav", "select.wav"},
                "late-stage-sound-members")
        sound_hashes = {}
        for name in names:
            with wave.open(str(sounds / name), "rb") as sound:
                require(sound.getparams()[:3] == (2, 3, 48000)
                        and sound.getnframes() < 24000,
                        "late-stage-sound-format")
            sound_hashes[name] = sha(sounds / name)
        require(len(set(sound_hashes.values())) == 4
                and len({sound_hashes[name] for name in
                         ("nav-down.wav", "nav-left.wav", "nav-right.wav", "nav-up.wav")}) == 1,
                "late-stage-sound-family")
        copy_files(sounds, sound_hashes,
                   output / "storage/.kodi/addons/resource.uisounds.asterhome/resources")

        startup = sources / "aster-startup-20261025"
        startup_manifest = json.loads((startup / "manifest.json").read_bytes())
        require(set(startup_manifest["files"]) == {"addon.xml", "service.py", "startup.wav"},
                "late-stage-startup-contract")
        copy_files(startup / "service.aster.startup", startup_manifest["files"],
                   output / "storage/.kodi/addons/service.aster.startup")

        idle = sources / "aster-idle-presentation5"
        idle_manifest = json.loads((idle / "manifest.json").read_bytes())
        require(idle_manifest.get("kind") == "hp-idle-presentation.v2"
                and idle_manifest.get("network") is False
                and idle_manifest.get("speech") is False,
                "late-stage-idle-contract")
        archive = idle / idle_manifest["archive"]
        require(sha(archive) == idle_manifest["archive_sha256"],
                "late-stage-idle-archive")
        extract(archive, output / "storage/.kodi/addons/screensaver.asterhome.v2lab",
                idle_manifest["files"], "screensaver.asterhome.v2lab/")

        result = {
            "applied": True,
            "books_files": len(book_manifest["files"]),
            "consumer_files": len(consumer_manifest["files"]),
            "mount_units": len(consumer_manifest["unit_sha256"]),
            "camera_files": len(camera_manifest["files"]),
            "camera_loopback_only": True,
            "sound_files": len(sound_hashes),
            "startup_files": len(startup_manifest["files"]),
            "screensaver_files": len(idle_manifest["files"]),
            "identities_provisioned": False,
        }
    finally:
        if output.exists():
            shutil.rmtree(output)
    require(not output.exists(), "late-stage-rollback")
    result["rolled_back"] = True
    return result
