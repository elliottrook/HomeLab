"""Build the deterministic inactive SA3 registration bundle."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile


REPO = Path(__file__).resolve().parents[2]
BUNDLE_NAME = "aster-sa3-registration-v1.tar.gz"
BUNDLE_SHA256 = "78a4fe9996e784814bc4130b8c849cc46e969f5a6e2511c8e2fb099a77b6ff54"
FILES = (
    "scripts/local-ai/sa3_registration_install.py",
    "scripts/local-ai/lab_hours_workloads.py",
    "scripts/local-ai/lab_hours_inactive_target.py",
    "scripts/local-ai/lab_hours_reservations.py",
    "scripts/local-ai/lab_hours_reserved_runner.py",
    "scripts/local-ai/lab_hours_release_manifest.json",
)


class BundleError(RuntimeError):
    pass


def _write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, data)
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def build(output_dir: Path) -> dict[str, object]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        info = output_dir.lstat()
        if not output_dir.is_dir() or output_dir.is_symlink() or info.st_mode & 0o777 != 0o700:
            raise BundleError("OUTPUT_CUSTODY_INVALID")
    else:
        output_dir.mkdir(mode=0o700)
        os.chmod(output_dir, 0o700)
    stage = output_dir / ".stage"
    if stage.exists():
        raise BundleError("STAGE_EXISTS")
    stage.mkdir(mode=0o700)
    try:
        rows = []
        for name in FILES:
            source = REPO / name
            if not source.is_file() or source.is_symlink():
                raise BundleError("SOURCE_INVALID:" + name)
            data = source.read_bytes()
            _write(stage / name, data, 0o644)
            rows.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "mode": "0644"})
        manifest = (json.dumps({"schema": "aster-sa3-registration-bundle.v1", "files": rows},
                               sort_keys=True, separators=(",", ":")) + "\n").encode()
        _write(stage / "bundle-manifest.json", manifest, 0o600)
        output = io.BytesIO()
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for name in sorted(FILES + ("bundle-manifest.json",)):
                    data = (stage / name).read_bytes()
                    info = tarfile.TarInfo(name)
                    info.size = len(data); info.mode = (stage / name).stat().st_mode & 0o777
                    info.uid = 0; info.gid = 0; info.uname = "root"; info.gname = "root"; info.mtime = 0
                    archive.addfile(info, io.BytesIO(data))
        data = output.getvalue()
        digest = hashlib.sha256(data).hexdigest()
        if digest != BUNDLE_SHA256:
            raise BundleError("BUNDLE_HASH_INVALID:" + digest)
        archive_path = output_dir / BUNDLE_NAME
        _write(archive_path, data, 0o600)
        sidecar = output_dir / (BUNDLE_NAME + ".sha256")
        _write(sidecar, f"{digest}  {BUNDLE_NAME}\n".encode(), 0o600)
        return {"archive": str(archive_path), "archive_sha256": digest,
                "sidecar": str(sidecar), "source_files": len(FILES),
                "effects": "not-attempted"}
    finally:
        shutil.rmtree(stage)


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.output_dir), sort_keys=True))
        return 0
    except (BundleError, OSError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
