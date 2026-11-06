#!/usr/bin/env python3
"""Render exact AsterTV placement assets directly from approved SVG masters."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import struct
import subprocess


TV_RELATIVE = Path("brands/aster-home/working/2026-11-04-approved-r5/SVG/32-aster-tv-logo.svg")
TV_SHA256 = "747aab438334afc9b1e2a0dafa8608bd8b8d4aa5ed29af5697f22972b714d2e8"
REMOTE_RELATIVE = Path("brands/aster-home/working/2026-11-05-aster-tv-remote-svg/SVG/AsterTV-Remote.svg")
REMOTE_SHA256 = "7effb1ffe3ba828de63059235c976f26e0d7fb869e0856d0fb52cea86a775ada"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"not-png:{path}")
    return struct.unpack(">II", data[16:24])


def render_svg(source: Path, width: int, height: int, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "/usr/bin/sips", "-s", "format", "png", "-z", str(height), str(width),
        str(source), "--out", str(output),
    ], check=True, timeout=180, stdout=subprocess.DEVNULL)
    if png_size(output) != (width, height):
        raise RuntimeError(f"placement-size-mismatch:{output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    tv = args.asset_root / TV_RELATIVE
    remote = args.asset_root / REMOTE_RELATIVE
    if sha(tv) != TV_SHA256 or sha(remote) != REMOTE_SHA256:
        raise RuntimeError("approved-svg-hash-mismatch")
    args.output.mkdir(parents=True, exist_ok=True)
    swift_environment = os.environ.copy()
    swift_environment["CLANG_MODULE_CACHE_PATH"] = "/private/tmp/astertv-swift-module-cache"
    swift_environment["SWIFT_MODULECACHE_PATH"] = "/private/tmp/astertv-swift-module-cache"
    subprocess.run([
        "/usr/bin/swift", str(Path(__file__).with_name("render_tv_splash.swift")),
        str(tv), str(args.output / "astertv-splash-1920x1080.png"),
    ], check=True, timeout=180, env=swift_environment)
    if png_size(args.output / "astertv-splash-1920x1080.png") != (1920, 1080):
        raise RuntimeError("placement-size-mismatch:astertv-splash-1920x1080.png")
    render_svg(remote, 180, 180, args.output / "astertv-remote-180.png")
    render_svg(remote, 512, 512, args.output / "astertv-remote-512.png")
    for path in sorted(args.output.iterdir()):
        print(f"{path.name} {png_size(path)[0]}x{png_size(path)[1]} {sha(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
