#!/usr/bin/env python3
"""Build deterministic private Aster Home Kodi add-on archives."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import zipfile


HERE = Path(__file__).resolve().parent
RELEASE = "1.1.1"
ADDONS = (
    "plugin.video.asterhome",
    "plugin.audio.asterbooks",
    "resource.uisounds.asterhome",
    "skin.asterhome",
)
OFFICIAL_DEPENDENCIES = (
    {"addon_id": "plugin.video.youtube", "version": "7.4.4",
     "source": "Kodi Omega repository"},
)
ZIP_TIME = (2026, 10, 23, 1, 0, 0)
CLIENT_FILES = (
    {
        "source": HERE / "remote" / "g20s-pro-plus.xml",
        "name": "g20s-pro-plus.xml",
        "install_target": "userdata/keymaps/g20s-pro-plus.xml",
    },
    {
        "source": HERE / "libreelec" / "aster-books-refresh.service",
        "name": "aster-books-refresh.service",
        "install_target": "/storage/.config/system.d/aster-books-refresh.service",
    },
    {
        "source": HERE / "libreelec" / "aster-books-refresh.timer",
        "name": "aster-books-refresh.timer",
        "install_target": "/storage/.config/system.d/aster-books-refresh.timer",
    },
)


def development_only(relative: Path) -> bool:
    parts = relative.parts
    name = relative.name
    if name in {".DS_Store", ".gitkeep", "README.md", "RELEASE.md"}:
        return True
    if "__pycache__" in parts or name.endswith((".pyc", ".pyo")):
        return True
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if parts and parts[0] == "tools":
        return name.startswith(("test_", "build_", "pilot_", "install_"))
    return relative.suffix.lower() == ".svg"


def package_files(addon: Path):
    return [path for path in sorted(addon.rglob("*"))
            if path.is_file() and not development_only(path.relative_to(addon))]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_archive(addon_id: str, output: Path, runtime_sounds: bool = False) -> dict:
    source = HERE / addon_id
    if not (source / "addon.xml").is_file():
        raise ValueError(f"missing add-on source: {source}")
    archive = output / f"{addon_id}-{RELEASE}.zip"
    records = []
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in package_files(source):
            relative = path.relative_to(source)
            member = Path(addon_id) / relative
            info = zipfile.ZipInfo(member.as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            data = path.read_bytes()
            if runtime_sounds and addon_id == 'resource.uisounds.asterhome' and relative.suffix == '.wav':
                from v2.canonical_sound_compat import promote
                data = promote(data)
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9)
            records.append({"path": member.as_posix(),
                            "sha256": hashlib.sha256(data).hexdigest(),
                            "bytes": len(data)})
    return {"addon_id": addon_id, "archive": archive.name,
            "sha256": sha256(archive), "bytes": archive.stat().st_size,
            "files": records}


def build(output: Path, runtime_sounds: bool = False) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError(f"output directory is not empty: {output}")
    archives = [build_archive(addon_id, output, runtime_sounds) for addon_id in ADDONS]
    client_files = []
    for record in CLIENT_FILES:
        data = record["source"].read_bytes()
        destination = output / record["name"]
        destination.write_bytes(data)
        os.chmod(destination, 0o644)
        client_files.append({
            "file": record["name"],
            "install_target": record["install_target"],
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })
    manifest = {
        "schema": "aster-home-kodi-release.v1",
        "release": RELEASE,
        "sound_encoding": "PCM32-lossless-from-PCM24" if runtime_sounds else "PCM24-source-reference-not-for-Kodi-runtime",
        "status": "production-candidate-pending-physical-libreelec-gate",
        "design_canvas": "1920x1080-16:9-scales-to-4k",
        "install_order": list(ADDONS),
        "external_dependencies": list(OFFICIAL_DEPENDENCIES),
        "archives": archives,
        "client_files": client_files,
    }
    manifest_path = output / f"aster-home-v{RELEASE}-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.chmod(manifest_path, 0o644)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime-sounds", action="store_true", help="Required for Kodi deployment: lossless PCM32 sound copies")
    args = parser.parse_args()
    manifest = build(args.output.resolve(), runtime_sounds=args.runtime_sounds)
    print(json.dumps({"release": manifest["release"],
                      "archives": [{"archive": item["archive"],
                                    "sha256": item["sha256"],
                                    "bytes": item["bytes"]}
                                   for item in manifest["archives"]]},
                     indent=2))


if __name__ == "__main__":
    main()
