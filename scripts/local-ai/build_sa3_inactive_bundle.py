"""Build the deterministic, root-custodied SA3 inactive staging bundle."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Iterable


REPO = Path(__file__).resolve().parents[2]
PACKET_REL = Path("services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json")
PACKET_SHA256 = "9173ea4179f16efcd635ca9eefe5d9f767b07dfee082e250f0a1a22a898b7a0c"
INSTALLER_REL = Path("scripts/local-ai/sa3_inactive_install.py")
BUNDLE_NAME = "aster-sa3-inactive-install-8dc6eac5.tar.gz"
STREAM_COMMIT = "434c5aedddd59665c7e2e8961196b81310e02765"


class BundleError(RuntimeError):
    pass


def _verify_dir(path: Path, uid: int) -> None:
    info = path.lstat()
    if not path.is_dir() or path.is_symlink() or info.st_uid != uid or info.st_mode & 0o777 != 0o700:
        raise BundleError(f"BUNDLE_DIR_CUSTODY_INVALID:{path}")


def _git_source(relative: str) -> bytes:
    result = subprocess.run(("git", "show", f"{STREAM_COMMIT}:{relative}"), cwd=REPO,
                            capture_output=True, check=False)
    if result.returncode != 0:
        raise BundleError(f"STREAM_SOURCE_MISSING:{relative}")
    return result.stdout


def _source_bytes(relative: str) -> bytes:
    if relative.startswith("services/aster-agent/evals/"):
        return _git_source(relative)
    path = REPO / relative
    if not path.is_file() or path.is_symlink():
        raise BundleError(f"SOURCE_MISSING:{relative}")
    return path.read_bytes()


def _write_file(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data)
        os.fchmod(fd, mode)
        os.fchown(fd, os.geteuid(), os.getegid())
        os.fsync(fd)
    finally:
        os.close(fd)


def _tar_bytes(root: Path, names: Iterable[str]) -> bytes:
    import io
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for name in sorted(names):
                path = root / name
                data = path.read_bytes()
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                info.mode = path.stat().st_mode & 0o777
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "root"
                info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def build(output_dir: Path, *, repo: Path = REPO, expected_uid: int | None = None,
          retain_stage: bool = False) -> dict[str, object]:
    expected_uid = os.geteuid() if expected_uid is None else expected_uid
    output_dir = Path(output_dir)
    if output_dir.exists():
        _verify_dir(output_dir, expected_uid)
    else:
        output_dir.mkdir(parents=True, mode=0o700)
        os.chmod(output_dir, 0o700)
        _verify_dir(output_dir, expected_uid)
    packet_path = repo / PACKET_REL
    packet_data = packet_path.read_bytes()
    if hashlib.sha256(packet_data).hexdigest() != PACKET_SHA256:
        raise BundleError("PACKET_HASH_INVALID")
    packet = json.loads(packet_data)
    if packet.get("schema") != "aster-lab-hours-sa3-inactive-install.v2":
        raise BundleError("PACKET_SCHEMA_INVALID")

    selected: dict[str, tuple[bytes, int]] = {
        str(PACKET_REL): (packet_data, 0o600),
        str(INSTALLER_REL): (_source_bytes(str(INSTALLER_REL)), 0o644),
    }
    for record in packet["host"]["install_files"]:
        selected[record["source"]] = (_source_bytes(record["source"]), 0o644)
    for record in packet["guest"]["runtime_files"]:
        selected[record["source"]] = (_source_bytes(record["source"]), 0o644)
    selected[packet["guest"]["wrapper"]["source"]] = (
        _source_bytes(packet["guest"]["wrapper"]["source"]), 0o644)
    if any("keys-v1" in name or "review" in name for name in selected):
        raise BundleError("EXCLUDED_REVIEW_MATERIAL_SELECTED")

    stage = output_dir / ".stage"
    if stage.exists():
        raise BundleError("STAGE_ALREADY_EXISTS")
    stage.mkdir(mode=0o700)
    os.chmod(stage, 0o700)
    try:
        _verify_dir(stage, expected_uid)
        manifest_files = []
        for name, (data, mode) in sorted(selected.items()):
            target = stage / name
            _write_file(target, data, mode)
            info = target.lstat()
            if info.st_uid != expected_uid or info.st_nlink != 1 or info.st_mode & 0o777 != mode:
                raise BundleError(f"STAGED_CUSTODY_INVALID:{name}")
            manifest_files.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "mode": f"{mode:04o}"})
        bundle_manifest = {
            "schema": "aster-sa3-inactive-bundle.v1",
            "packet_sha256": PACKET_SHA256,
            "source_commits": packet["source_commits"],
            "files": manifest_files,
            "retention": "retain archive and sidecar; remove transient extracted stage after authorized postcheck/rollback retention window",
        }
        manifest_data = (json.dumps(bundle_manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
        _write_file(stage / "bundle-manifest.json", manifest_data, 0o600)
        archive_data = _tar_bytes(stage, list(selected) + ["bundle-manifest.json"])
        archive_path = output_dir / BUNDLE_NAME
        _write_file(archive_path, archive_data, 0o600)
        digest = hashlib.sha256(archive_data).hexdigest()
        sidecar = output_dir / (BUNDLE_NAME + ".sha256")
        _write_file(sidecar, f"{digest}  {BUNDLE_NAME}\n".encode(), 0o600)
        return {"archive": str(archive_path), "archive_sha256": digest,
                "sidecar": str(sidecar), "stage": str(stage) if retain_stage else None,
                "source_files": len(selected), "effects": "not-attempted"}
    finally:
        if not retain_stage:
            shutil.rmtree(stage, ignore_errors=False)


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--retain-stage", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.output_dir, retain_stage=args.retain_stage), sort_keys=True))
        return 0
    except (BundleError, OSError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
