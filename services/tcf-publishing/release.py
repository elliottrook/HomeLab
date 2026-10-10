"""Prepare and atomically activate immutable static site releases."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil

from content import ContentError, SITES
from template_candidate import BANNER, BANNER_STYLE


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


def _write_manifest(directory: Path) -> None:
    entries = []
    for path in sorted(item for item in directory.rglob("*") if item.is_file()
                       and item.name != "MANIFEST.sha256"):
        entries.append(f"{sha256(path.read_bytes()).hexdigest()}  ./{path.relative_to(directory).as_posix()}")
    (directory / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def prepare_release(candidate: Path, destination: Path, expected_site: str) -> dict:
    if expected_site not in SITES:
        raise ContentError("unknown release site")
    if destination.exists():
        raise ContentError("release destination already exists")
    verify_manifest(candidate)
    metadata_path = candidate / "candidate.json"
    if not metadata_path.is_file():
        raise ContentError("candidate metadata is missing")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("site") != expected_site or not isinstance(metadata.get("edition_id"), int):
        raise ContentError("candidate site or edition is invalid")
    shutil.copytree(candidate, destination, symlinks=False)
    for page in destination.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        if "SAMPLE — NOT FOR PUBLICATION" in text:
            shutil.rmtree(destination)
            raise ContentError("sample content cannot become a release")
        text = text.replace(BANNER, "").replace(BANNER_STYLE, "")
        page.write_text(text, encoding="utf-8")
    (destination / "candidate.json").unlink()
    _write_manifest(destination)
    digest = verify_manifest(destination)
    release_id = f"{expected_site}-e{metadata['edition_id']}-{digest[:12]}"
    return {"site": expected_site, "edition_id": metadata["edition_id"],
            "release_id": release_id, "manifest_sha256": digest}


def activate_release(release: Path, releases_root: Path, current_link: Path) -> str | None:
    """Switch a same-filesystem symlink only after complete verification."""
    verify_manifest(release)
    resolved_root = releases_root.resolve()
    resolved_release = release.resolve()
    if not resolved_release.is_relative_to(resolved_root) or release.parent != releases_root:
        raise ContentError("release is outside the immutable release root")
    previous = os.readlink(current_link) if current_link.is_symlink() else None
    temporary = current_link.with_name(current_link.name + ".next")
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    os.symlink(resolved_release, temporary)
    os.replace(temporary, current_link)
    return previous
