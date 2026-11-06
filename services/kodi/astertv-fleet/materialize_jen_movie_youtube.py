#!/usr/bin/env python3
"""Materialize Jen Movie/YouTube while excluding private session state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/m4"
RECOVERED = SOURCE / "recovered"
APPLY = SOURCE / "apply_jen_movie_youtube_composed.py"
EXPECTED = {
    "movie/custom_1130_movie.xml": "ec69ea074ed0ef7cd6f5c810ba35b437d612a1f27d300f93be96762de927164a",
    "movie/movie.py": "bdb3384e507672ac7c0acfe1f5699a2a360eb383bb51ec990967c51fe7af201d",
    "movie/jellyfin_trailer_route.py": "a94454d3a33fa64c49a8ddaa5b5f1c1df91de2400af1dd7f76df128b5d56888a",
    "movie/select_dispatch.py": "d72d82630a5b0a172f5c8ba7b11d51ad04cadb80500fbcfbd48da9d7374397e3",
    "movie/select_dispatch.overlay.py": "0a0d80545259cc390f03ff971a98eed19549194fed1bac42bb879ad697372cc3",
    "movie/manifest.json": "92e6026774c9cac14353bc155a38013da0bcb6e652ce3db0bb9e3a9abe604707",
    "youtube/MyVideoNav.base.xml": "6798822d0218b96cde69e385545ad36a425c01c455fdfcb69a5d8ab7208fcf8a",
    "youtube/MyVideoNav.xml": "bdba7dd50a03b51eb35fdf3d0a31b03398e5dfe22063260d1cb1477933b4bc33",
    "youtube/youtube_root_focus.py": "879dcd143cff8f0aa339438195d41756c4fa0549ea74ae859d2600a45ce64e15",
    "youtube/graceful_kodi_stop.py": "00fa1cab4c5cea6f96ed9ee4527768e798a3dceb025a6f19fa1473833176d24d",
    "youtube/50-astertv-graceful-stop.conf": "c69ca2669713568baac5a5d211f55b19a96c57fb1b1da7725c84fe9034b6dc6c",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def read(relative: str) -> bytes:
    data = (RECOVERED / relative).read_bytes()
    if sha(data) != EXPECTED[relative]:
        raise RuntimeError("jen-movie-youtube-recovery-drift:" + relative)
    return data


def render() -> tuple[dict[str, tuple[bytes, str, str]], dict]:
    movie_xml = read("movie/custom_1130_movie.xml")
    sources = {
        relative: read(relative) for relative in EXPECTED
    }
    unit = (
        "[Unit]\nDescription=Apply composed AsterTV v3 Movie and YouTube on Jen\n"
        "After=astertv-release-guard.service\nBefore=kodi.service\n"
        "[Service]\nType=oneshot\n"
        "ExecStart=/usr/bin/python3 /storage/.aster-v3/m4-composed/apply.py\n"
        "[Install]\nWantedBy=kodi.service\n"
    ).encode()
    live = {
        "live/skin.asterhome/1080i/custom_1130_movie.xml":
            (movie_xml, "/storage/.kodi/addons/skin.asterhome/1080i/custom_1130_movie.xml", "0644"),
        "live/aster-global-search-ui22/overlay/custom_1130_movie.xml":
            (movie_xml, "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/overlay/custom_1130_movie.xml", "0644"),
        "live/aster-global-search-ui22/movie.py":
            (sources["movie/movie.py"], "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/movie.py", "0755"),
        "live/aster-global-search-ui22/jellyfin_trailer_route.py":
            (sources["movie/jellyfin_trailer_route.py"], "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/jellyfin_trailer_route.py", "0755"),
        "live/skin.asterhome/tools/select_dispatch.py":
            (sources["movie/select_dispatch.py"], "/storage/.kodi/addons/skin.asterhome/tools/select_dispatch.py", "0755"),
        "live/aster-global-search-ui22/overlay/select_dispatch.py":
            (sources["movie/select_dispatch.overlay.py"], "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/overlay/select_dispatch.py", "0755"),
        "live/aster-global-search-ui22/manifest.json":
            (sources["movie/manifest.json"], "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/manifest.json", "0644"),
        "live/skin.asterhome/1080i/MyVideoNav.xml":
            (sources["youtube/MyVideoNav.xml"], "/storage/.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml", "0644"),
        "live/skin.asterhome/tools/youtube_root_focus.py":
            (sources["youtube/youtube_root_focus.py"], "/storage/.kodi/addons/skin.asterhome/tools/youtube_root_focus.py", "0755"),
    }
    stable_map = {
        "movie/custom_1130_movie.xml": movie_xml,
        "movie/custom_1130_movie.overlay.xml": movie_xml,
        "movie/movie.py": sources["movie/movie.py"],
        "movie/jellyfin_trailer_route.py": sources["movie/jellyfin_trailer_route.py"],
        "movie/select_dispatch.py": sources["movie/select_dispatch.py"],
        "movie/select_dispatch.overlay.py": sources["movie/select_dispatch.overlay.py"],
        "movie/manifest.json": sources["movie/manifest.json"],
        "youtube/MyVideoNav.xml": sources["youtube/MyVideoNav.xml"],
        "youtube/youtube_root_focus.py": sources["youtube/youtube_root_focus.py"],
    }
    files = dict(live)
    for relative, data in stable_map.items():
        files["stable/payload/" + relative] = (
            data, "/storage/.aster-v3/m4-composed/payload/" + relative, "0600")
    files.update({
        "stable/apply.py": (APPLY.read_bytes(), "/storage/.aster-v3/m4-composed/apply.py", "0600"),
        "stable/graceful_kodi_stop.py": (sources["youtube/graceful_kodi_stop.py"], "/storage/.aster-v3/m4-composed/graceful_kodi_stop.py", "0600"),
        "system.d/astertv-v3-m4-composed-jen.service": (unit, "/storage/.config/system.d/astertv-v3-m4-composed-jen.service", "0644"),
        "system.d/kodi.service.d/50-astertv-graceful-stop.conf":
            (sources["youtube/50-astertv-graceful-stop.conf"],
             "/storage/.config/system.d/kodi.service.d/50-astertv-graceful-stop.conf", "0644"),
    })
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-movie-youtube",
        "provenance": {"checkpoint": ["astertv-v3-m4-jen-movie", "astertv-v3-m4y-jen"],
                       "accepted_hashes": EXPECTED},
        "files": [
            {"destination": destination, "bytes": len(data),
             "sha256": sha(data), "mode": mode}
            for _, (data, destination, mode) in sorted(files.items())
        ],
        "mutable_state": [
            {"path": "/storage/.kodi/userdata/addon_data/plugin.video.youtube",
             "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/Database/Addons33.db",
             "bundled": False, "sensitive": False},
            {"path": "/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab",
             "bundled": False, "sensitive": True, "owner": "jen-account-registry"},
        ],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, tuple[bytes, str, str]], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, (data, _, mode) in sorted(files.items()):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, int(mode, 8)); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-movie-youtube")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
