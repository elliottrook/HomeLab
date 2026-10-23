#!/usr/bin/env python3
"""Compose the startup splash from the approved AsterTV logo export.

Requires Pillow. The source ZIP is intentionally not committed to this repo.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import zipfile

from PIL import Image


ARCHIVE_SHA256 = "6a888ef158f9272f56e73c84494b20c7d7190a6e474deed403e6c72b474c95b0"
LOGO_SHA256 = "f54e9e3da5b03b99e0fd2fc25ca903b8bdc6fe0893612a893cbe21b31b9c412e"
LOGO_PATH = "aster-brand-v2-tv-2026-10-22/PNG/32-aster-tv-logo-1254.png"
CANVAS = (1920, 1080)
BACKGROUND = "#20251f"
LOGO_WIDTH = 700


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("Approved AsterTV archive checksum mismatch")
    with zipfile.ZipFile(args.archive) as package:
        source = package.read(LOGO_PATH)
    if hashlib.sha256(source).hexdigest() != LOGO_SHA256:
        raise SystemExit("Approved AsterTV logo checksum mismatch")

    logo = Image.open(BytesIO(source)).convert("RGBA")
    height = round(logo.height * LOGO_WIDTH / logo.width)
    logo = logo.resize((LOGO_WIDTH, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, BACKGROUND)
    canvas.alpha_composite(logo, ((CANVAS[0] - LOGO_WIDTH) // 2, (CANVAS[1] - height) // 2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(args.output, optimize=True)


if __name__ == "__main__":
    main()
