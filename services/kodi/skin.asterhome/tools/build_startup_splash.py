#!/usr/bin/env python3
"""Compose Kodi's startup splash from the approved Aster v2 logo export.

Requires Pillow. The source ZIP is intentionally not committed to this repo.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import zipfile

from PIL import Image


ARCHIVE_SHA256 = "2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc"
LOGO_SHA256 = "2ce7d212b4f42812fc8d343fdb429f579707ffdcc72da10ec6b2af5065a9d461"
LOGO_PATH = "PNG/1254/14-aster-home-logo.png"
CANVAS = (1920, 1080)
BACKGROUND = "#20251f"
LOGO_WIDTH = 700


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("Approved Aster v2 archive checksum mismatch")
    with zipfile.ZipFile(args.archive) as package:
        source = package.read(LOGO_PATH)
    if hashlib.sha256(source).hexdigest() != LOGO_SHA256:
        raise SystemExit("Approved Aster Home logo checksum mismatch")

    logo = Image.open(BytesIO(source)).convert("RGBA")
    height = round(logo.height * LOGO_WIDTH / logo.width)
    logo = logo.resize((LOGO_WIDTH, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, BACKGROUND)
    canvas.alpha_composite(logo, ((CANVAS[0] - LOGO_WIDTH) // 2, (CANVAS[1] - height) // 2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(args.output, optimize=True)


if __name__ == "__main__":
    main()
