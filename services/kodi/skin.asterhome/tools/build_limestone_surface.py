#!/usr/bin/env python3
"""Render the approved Aster v2 limestone layer without its compass artwork.

This is a source-derived material asset, not a new interpretation of the logo.
The input release archive is deliberately not checked into the Kodi skin.
"""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile


ARCHIVE_SHA256 = "2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc"
SOURCE_SHA256 = "f6a0f19ff9e5ac4728e04cf20c28e86f171d516ec403a1bc3df937c8a456c6a4"
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("Approved Aster v2 archive checksum mismatch")
    with zipfile.ZipFile(args.archive) as package:
        original = package.read("SVG/01-aster.svg")
    if hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Approved Aster v2 source checksum mismatch")

    source = ET.fromstring(original)
    limestone = source.find(f"{{{SVG}}}g[@id='limestone-tile']")
    definitions = source.find(f"{{{SVG}}}defs")
    if limestone is None or definitions is None:
        raise SystemExit("Approved limestone layer is missing")
    for child in list(source):
        if child is not definitions and child is not limestone:
            source.remove(child)
    # Keep source coordinates intact; the raster is an exact layer-only render.
    svg = ET.tostring(source, encoding="utf-8")
    node = os.environ.get("ASTER_NODE", "/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
    package_path = os.environ.get("ASTER_SHARP", "/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp")
    code = """
const sharp=require(process.argv[1]);
let chunks=[];
process.stdin.on('data',c=>chunks.push(c));
process.stdin.on('end',async()=>{
  const full=await sharp(Buffer.concat(chunks)).resize(512,512).png().toBuffer();
  // The compass overlays the centre; this upper mineral band is unobstructed.
  const stone=await sharp(full).extract({left:74,top:35,width:155,height:51})
    .resize(280,56).png().toBuffer();
  const wash={input:Buffer.from('<svg width="280" height="56"><rect width="280" height="56" fill="#f3ede2" opacity="0.38"/></svg>')};
  const mask={input:Buffer.from('<svg width="280" height="56"><rect width="280" height="56" rx="20" fill="white"/></svg>'),blend:'dest-in'};
  await sharp(stone).composite([wash,mask]).png().toFile(process.argv[2]);
});
"""
    subprocess.run([node, "-e", code, package_path, str(args.output)], input=svg, check=True)


if __name__ == "__main__":
    main()
