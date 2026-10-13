"""Verify and atomically activate immutable Fotosforfun static releases."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil

from model import ContentError
from renderer import PLACEHOLDER_NOTICE, write_manifest


def verify_manifest(directory: Path) -> str:
    manifest = directory / "MANIFEST.sha256"
    if not directory.is_dir() or not manifest.is_file():
        raise ContentError("release manifest is missing")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  \./(.+)", line)
        if not match:
            raise ContentError("release manifest is malformed")
        relative = PurePosixPath(match.group(2))
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() == "MANIFEST.sha256":
            raise ContentError("release manifest contains an unsafe path")
        if relative.as_posix() in expected:
            raise ContentError("release manifest contains a duplicate path")
        expected[relative.as_posix()] = match.group(1)
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*")
              if path.is_file() and path.name != "MANIFEST.sha256"}
    if actual != set(expected):
        raise ContentError("release files do not match the manifest")
    for relative, digest in expected.items():
        if sha256((directory / relative).read_bytes()).hexdigest() != digest:
            raise ContentError(f"release checksum mismatch: {relative}")
    return sha256(manifest.read_bytes()).hexdigest()


def prepare_release(candidate: Path, releases_root: Path) -> dict[str, str]:
    verify_manifest(candidate)
    metadata_path = candidate / "candidate.json"
    if not metadata_path.is_file():
        raise ContentError("candidate metadata is missing")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    catalogue = metadata.get("catalogueSha256")
    if (metadata.get("site") != "fotosforfun" or metadata.get("samples") is not False
            or not isinstance(metadata.get("photoCount"), int) or metadata["photoCount"] < 1
            or not isinstance(catalogue, str) or not re.fullmatch(r"[0-9a-f]{64}", catalogue)):
        raise ContentError("candidate metadata is invalid or contains samples")
    if PLACEHOLDER_NOTICE in (candidate / "index.html").read_text(encoding="utf-8"):
        raise ContentError("sample disclosure cannot become a public release")
    releases_root.mkdir(parents=True, exist_ok=True)
    staging = releases_root / f".prepare-{catalogue[:12]}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(candidate, staging, symlinks=False)
    try:
        (staging / "candidate.json").unlink()
        write_manifest(staging)
        final_digest = verify_manifest(staging)
        release_id = f"fotosforfun-{catalogue[:12]}-{final_digest[:12]}"
        destination = releases_root / release_id
        if destination.exists():
            existing = verify_manifest(destination)
            if existing != final_digest:
                raise ContentError("release id already exists with different content")
            return {"releaseId": release_id, "manifestSha256": existing,
                    "catalogueSha256": catalogue}
        os.replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {"releaseId": release_id, "manifestSha256": final_digest,
            "catalogueSha256": catalogue}


def activate_release(release: Path, releases_root: Path, current_link: Path) -> str | None:
    verify_manifest(release)
    root = releases_root.resolve()
    target = release.resolve()
    if release.parent.resolve() != root or not target.is_relative_to(root):
        raise ContentError("release is outside the immutable release root")
    previous = os.readlink(current_link) if current_link.is_symlink() else None
    temporary = current_link.with_name(current_link.name + ".next")
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    os.symlink(target, temporary)
    os.replace(temporary, current_link)
    return previous
