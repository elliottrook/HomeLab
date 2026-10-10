#!/usr/bin/python3
"""Forced-command receiver for checksum-verified TCF releases."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import sys
import tarfile


ROOT = Path(os.environ.get("TCF_ORIGIN_ROOT", "/srv/tcf/sites"))
SITES = {"contrast", "closet"}
RELEASE_ID = re.compile(r"(?:contrast|closet)-e[1-9][0-9]*-[0-9a-f]{12}")


class ReceiverError(ValueError):
    pass


def verify(directory: Path) -> str:
    manifest = directory / "MANIFEST.sha256"
    if not manifest.is_file():
        raise ReceiverError("manifest missing")
    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  \./(.+)", line)
        if not match:
            raise ReceiverError("malformed manifest")
        relative = PurePosixPath(match.group(2))
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() == "MANIFEST.sha256":
            raise ReceiverError("unsafe manifest path")
        if relative.as_posix() in expected:
            raise ReceiverError("duplicate manifest path")
        expected[relative.as_posix()] = match.group(1)
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*")
              if path.is_file() and path.name != "MANIFEST.sha256"}
    if actual != set(expected):
        raise ReceiverError("file inventory mismatch")
    for relative, digest in expected.items():
        path = directory / relative
        if path.is_symlink() or sha256(path.read_bytes()).hexdigest() != digest:
            raise ReceiverError("checksum mismatch")
    for page in directory.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        if "PRIVATE CANDIDATE" in text or "SAMPLE — NOT FOR PUBLICATION" in text:
            raise ReceiverError("non-public marker present")
    if (directory / "candidate.json").exists():
        raise ReceiverError("private candidate metadata present")
    return sha256(manifest.read_bytes()).hexdigest()


def _site(site: str) -> Path:
    if site not in SITES:
        raise ReceiverError("unknown site")
    return ROOT / site


def extract_archive(stream, destination: Path) -> None:
    """Extract only regular files and directories beneath destination."""
    with tarfile.open(fileobj=stream, mode="r|*") as archive:
        for member in archive:
            relative = PurePosixPath(member.name)
            if (relative.is_absolute() or ".." in relative.parts
                    or not relative.parts
                    or not (member.isdir() or member.isfile())):
                raise ReceiverError("archive contains unsafe member")
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o750)
            else:
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
                source = archive.extractfile(member)
                if source is None:
                    raise ReceiverError("archive member could not be read")
                with target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(0o640)


def stage(site: str, release_id: str) -> dict:
    if not RELEASE_ID.fullmatch(release_id) or not release_id.startswith(site + "-"):
        raise ReceiverError("invalid release id")
    site_root = _site(site)
    releases = site_root / "releases"
    staging = site_root / "staging"
    destination = releases / release_id
    if destination.exists():
        raise ReceiverError("release already exists")
    temporary = staging / f"{release_id}.partial-{os.getpid()}"
    temporary.mkdir(parents=True, mode=0o750)
    try:
        extract_archive(sys.stdin.buffer, temporary)
        digest = verify(temporary)
        releases.mkdir(parents=True, exist_ok=True, mode=0o750)
        os.replace(temporary, destination)
        return {"status": "staged", "site": site, "release_id": release_id,
                "manifest_sha256": digest}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def activate(site: str, release_id: str, expected_digest: str) -> dict:
    if not RELEASE_ID.fullmatch(release_id) or not release_id.startswith(site + "-"):
        raise ReceiverError("invalid release id")
    site_root = _site(site)
    release = site_root / "releases" / release_id
    digest = verify(release)
    if digest != expected_digest:
        raise ReceiverError("manifest digest does not match activation request")
    current = site_root / "current"
    previous_target = os.readlink(current) if current.is_symlink() else None
    previous = site_root / "previous"
    if previous_target:
        previous_next = site_root / "previous.next"
        if previous_next.is_symlink():
            previous_next.unlink()
        os.symlink(previous_target, previous_next)
        os.replace(previous_next, previous)
    current_next = site_root / "current.next"
    if current_next.is_symlink():
        current_next.unlink()
    os.symlink(release.resolve(), current_next)
    os.replace(current_next, current)
    return {"status": "active", "site": site, "release_id": release_id,
            "manifest_sha256": digest, "previous": previous_target}


def status() -> dict:
    return {site: {name: os.readlink(_site(site) / name)
                   if (_site(site) / name).is_symlink() else None
                   for name in ("current", "previous")} for site in sorted(SITES)}


def main() -> int:
    try:
        command = shlex.split(os.environ.get("SSH_ORIGINAL_COMMAND", "status"))
        if command == ["status"]:
            result = status()
        elif len(command) == 3 and command[0] == "stage":
            result = stage(command[1], command[2])
        elif len(command) == 4 and command[0] in {"activate", "rollback"}:
            result = activate(command[1], command[2], command[3])
        else:
            raise ReceiverError("command is not permitted")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ReceiverError, OSError, tarfile.TarError, UnicodeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "rejected", "detail": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
