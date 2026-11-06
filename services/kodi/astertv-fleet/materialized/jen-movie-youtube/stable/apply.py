#!/usr/bin/env python3
"""Reapply Jen's final Movie/YouTube payload without identity rewrites."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import socket

HOST = "AsterTV-Jen"
ROOT = Path("/storage/.aster-v3/m4-composed/payload")

TARGETS = {
    "movie/custom_1130_movie.xml": Path("/storage/.kodi/addons/skin.asterhome/1080i/custom_1130_movie.xml"),
    "movie/custom_1130_movie.overlay.xml": Path("/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/overlay/custom_1130_movie.xml"),
    "movie/movie.py": Path("/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/movie.py"),
    "movie/jellyfin_trailer_route.py": Path("/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/jellyfin_trailer_route.py"),
    "movie/select_dispatch.py": Path("/storage/.kodi/addons/skin.asterhome/tools/select_dispatch.py"),
    "movie/select_dispatch.overlay.py": Path("/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/overlay/select_dispatch.py"),
    "movie/manifest.json": Path("/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/manifest.json"),
    "youtube/MyVideoNav.xml": Path("/storage/.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml"),
    "youtube/youtube_root_focus.py": Path("/storage/.kodi/addons/skin.asterhome/tools/youtube_root_focus.py"),
}


def atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name("." + destination.name + ".m4-composed")
    shutil.copy2(source, temporary)
    os.chmod(temporary, 0o755 if destination.suffix == ".py" else 0o644)
    os.replace(temporary, destination)


def main() -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    for relative, destination in TARGETS.items():
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            raise RuntimeError("composed-payload-missing:" + relative)
        atomic(source, destination)


if __name__ == "__main__":
    main()
