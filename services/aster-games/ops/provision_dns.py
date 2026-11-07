#!/usr/bin/env python3
"""Add the two private Aster Games names to one Pi-hole v6 TOML file."""

import argparse
import os
from pathlib import Path
import shutil
import tempfile


RECORDS = (
    '    "192.168.50.23 games.elliottrook.com",',
    '    "192.168.50.23 romarr.elliottrook.com",',
)
ANCHOR = '    "192.168.20.37 aster-voice.home.internal"'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--backup", required=True, type=Path)
    args = parser.parse_args()
    content = args.config.read_text(encoding="utf-8")
    if all(record.rstrip(",") in content for record in RECORDS):
        print("private DNS records already present")
        return
    if any(record.rstrip(",") in content for record in RECORDS) or content.count(ANCHOR) != 1:
        raise RuntimeError("Pi-hole hosts anchor or partial-state drift")
    args.backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.config, args.backup)
    replacement = "\n".join(RECORDS) + "\n" + ANCHOR
    updated = content.replace(ANCHOR, replacement)
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-games-dns-", dir=args.config.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        metadata = args.config.stat()
        os.chmod(temporary, metadata.st_mode & 0o777)
        os.chown(temporary, metadata.st_uid, metadata.st_gid)
        os.replace(temporary, args.config)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("private DNS records added")


if __name__ == "__main__":
    main()
