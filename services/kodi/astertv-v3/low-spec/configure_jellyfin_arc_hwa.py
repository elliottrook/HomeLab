#!/usr/bin/env python3
"""Enable the reviewed Intel Arc full-transcode pipeline in Jellyfin."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import socket
import tempfile
import xml.etree.ElementTree as ET


HOST = "truenas"
EXPECTED_SHA256 = "14e8c711eba4f1f7bf6b065a8a430a4328bfe114d3483b39687a61a6b22f7676"
CODECS = ("h264", "hevc", "mpeg2video", "vc1", "vp9", "av1")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def configure(data: bytes) -> bytes:
    root = ET.fromstring(data)
    required = {
        "HardwareAccelerationType": "qsv",
        "VaapiDevice": "/dev/dri/renderD128",
        "EnableHardwareEncoding": "true",
    }
    for name, expected in required.items():
        node = root.find(name)
        if node is None or (node.text or "") != expected:
            raise RuntimeError(f"unexpected-{name}")

    opencl = root.find("EnableTonemapping")
    vpp = root.find("EnableVppTonemapping")
    if opencl is None or vpp is None:
        raise RuntimeError("missing-tone-mapping-setting")
    # This Jellyfin container exposes Intel VPP but no OpenCL platform.  When
    # OpenCL tone mapping is enabled Jellyfin still initializes it before VPP
    # and aborts the whole transcode.  Use the zero-copy Intel VPP path alone.
    opencl.text = "false"
    vpp.text = "true"

    codecs = root.find("HardwareDecodingCodecs")
    if codecs is None:
        raise RuntimeError("missing-HardwareDecodingCodecs")
    for child in list(codecs):
        codecs.remove(child)
    for codec in CODECS:
        ET.SubElement(codecs, "string").text = codec

    ET.indent(root, space="  ")
    return b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n"


def atomic_write(path: Path, data: bytes) -> None:
    fd, candidate = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(candidate, path.stat().st_mode & 0o777)
        os.replace(candidate, path)
    finally:
        try:
            os.unlink(candidate)
        except FileNotFoundError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("/mnt/Media/appdata/jellyfin/encoding.xml"))
    parser.add_argument("--hostname", default=socket.gethostname())
    args = parser.parse_args()
    if args.hostname != HOST:
        raise SystemExit(f"host-refused:{args.hostname}")
    original = args.config.read_bytes()
    if digest(original) != EXPECTED_SHA256:
        raise SystemExit("encoding-config-drift")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    checkpoint = args.config.parent / ".aster-checkpoints" / f"arc-hwa-{stamp}"
    checkpoint.mkdir(parents=True, mode=0o700)
    shutil.copy2(args.config, checkpoint / args.config.name)
    (checkpoint / "SHA256SUMS").write_text(f"{digest(original)}  {args.config.name}\n")
    os.chmod(checkpoint / "SHA256SUMS", 0o600)

    updated = configure(original)
    ET.fromstring(updated)
    atomic_write(args.config, updated)
    print(f"checkpoint={checkpoint}")
    print(f"updated_sha256={digest(updated)}")


if __name__ == "__main__":
    main()
