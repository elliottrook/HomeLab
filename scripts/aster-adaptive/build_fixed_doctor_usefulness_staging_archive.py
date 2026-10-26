"""Build the deterministic eight-file fixed Doctor staging archive."""

from __future__ import annotations

import argparse
import gzip
import io
import tarfile
from pathlib import Path


SOURCES = {
    "fixed-doctor-usefulness-v1.json": "fixtures/fixed-doctor-usefulness-v1.json",
    "fixed-doctor-usefulness-profile-v1.json": "fixtures/fixed-doctor-usefulness-profile-v1.json",
    "fixed_doctor_usefulness.py": "fixed_doctor_usefulness.py",
    "fixed_doctor_usefulness_capture.py": "fixed_doctor_usefulness_capture.py",
    "journaled_fixed_doctor_usefulness_capture.py": "journaled_fixed_doctor_usefulness_capture.py",
    "fixed_doctor_usefulness_9b_adapter.py": "fixed_doctor_usefulness_9b_adapter.py",
    "fixed_doctor_usefulness_profile.py": "fixed_doctor_usefulness_profile.py",
    "run_fixed_doctor_usefulness.py": "run_fixed_doctor_usefulness.py",
}


def build(source_directory: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    with output.open("xb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                for target_name, source_name in sorted(SOURCES.items()):
                    raw = (source_directory / source_name).read_bytes()
                    info = tarfile.TarInfo(target_name)
                    info.size = len(raw)
                    info.mode = 0o600
                    info.uid = 0
                    info.gid = 0
                    info.uname = "root"
                    info.gname = "root"
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(raw))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    build(args.source_directory, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
