"""Build deterministic no-execution candidate-g runner activation bundle."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile


REPO = Path(__file__).resolve().parents[2]
NAME = "aster-sa3-envelope-runner-activation-v1.tar.gz"
BUNDLE_SHA256 = "68ba4a16129b17f2e2ed2fc8c8a0f9e8236b7a1dda05f602f9766362b03f38d0"
FILES = (
    "scripts/local-ai/sa3_evidence_envelope_runner_activation_install.py",
    "scripts/local-ai/full_inference_lab_runtime.py",
    "scripts/local-ai/lab_hours_reserved_runner.py",
    "scripts/local-ai/lab_hours_release_manifest.json",
)


def build(output_directory: Path) -> dict[str, object]:
    output_directory = Path(output_directory)
    if output_directory.exists():
        info = output_directory.lstat()
        if (not output_directory.is_dir() or output_directory.is_symlink()
                or info.st_mode & 0o777 != 0o700):
            raise ValueError("OUTPUT_INVALID")
    else:
        output_directory.mkdir(mode=0o700)
    rows = []
    values = {}
    for name in FILES:
        path = REPO / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("SOURCE_INVALID:" + name)
        data = path.read_bytes()
        values[name] = data
        rows.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                     "mode": "0644"})
    values["bundle-manifest.json"] = (json.dumps({
        "schema": "aster-sa3-envelope-runner-activation-bundle.v1", "files": rows},
        sort_keys=True, separators=(",", ":")) + "\n").encode()
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as archive:
        with tarfile.open(fileobj=archive, mode="w") as tar:
            for name in sorted(values):
                data = values[name]
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o600 if name == "bundle-manifest.json" else 0o644
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = "root"
                tar.addfile(info, io.BytesIO(data))
    data = buffer.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    if BUNDLE_SHA256 and digest != BUNDLE_SHA256:
        raise ValueError("BUNDLE_HASH_INVALID:" + digest)
    path = output_directory / NAME
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, data)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return {"archive": str(path), "archive_sha256": digest,
            "files": len(FILES), "effects": "not-attempted"}


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.output_dir), sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
