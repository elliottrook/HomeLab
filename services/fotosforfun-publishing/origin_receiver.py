#!/usr/bin/python3
"""Forced-command receiver restricted to verified Fotosforfun releases."""

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


ROOT = Path("/srv/fotosforfun")
RELEASE_ID = re.compile(r"fotosforfun-[0-9a-f]{12}-[0-9a-f]{12}")


class ReceiverError(ValueError):
    pass


def verify(directory: Path, *, allow_private_sample: bool = False) -> str:
    manifest = directory / "MANIFEST.sha256"
    if not manifest.is_file() or manifest.is_symlink():
        raise ReceiverError("manifest missing")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  \./(.+)", line)
        if not match:
            raise ReceiverError("malformed manifest")
        relative = PurePosixPath(match.group(2))
        name = relative.as_posix()
        if relative.is_absolute() or ".." in relative.parts or name == "MANIFEST.sha256" or name in expected:
            raise ReceiverError("unsafe manifest path")
        expected[name] = match.group(1)
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*")
              if path.is_file() and path.name != "MANIFEST.sha256"}
    if actual != set(expected):
        raise ReceiverError("file inventory mismatch")
    for relative, digest in expected.items():
        path = directory / relative
        if path.is_symlink() or sha256(path.read_bytes()).hexdigest() != digest:
            raise ReceiverError("checksum mismatch")
    if (directory / "candidate.json").exists():
        raise ReceiverError("private candidate metadata present")
    html = "\n".join(path.read_text(encoding="utf-8") for path in directory.glob("*.html"))
    if (not allow_private_sample
            and ("credited photographs are stand-ins" in html or "SAMPLE" in html.upper())):
        raise ReceiverError("sample marker present")
    return sha256(manifest.read_bytes()).hexdigest()


def extract(stream, destination: Path) -> None:
    with tarfile.open(fileobj=stream, mode="r|*") as archive:
        for member in archive:
            relative = PurePosixPath(member.name)
            if (relative.is_absolute() or ".." in relative.parts or not relative.parts
                    or not (member.isdir() or member.isfile())):
                raise ReceiverError("archive contains unsafe member")
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o750)
            else:
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
                source = archive.extractfile(member)
                if source is None:
                    raise ReceiverError("archive member unavailable")
                with target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(0o640)


def stage(release_id: str) -> dict[str, str]:
    if not RELEASE_ID.fullmatch(release_id):
        raise ReceiverError("invalid release id")
    destination = ROOT / "releases" / release_id
    if destination.exists():
        digest = verify(destination)
        if not release_id.endswith(digest[:12]):
            raise ReceiverError("release id does not match manifest")
        return {"status": "already-staged", "release_id": release_id,
                "manifest_sha256": digest}
    temporary = ROOT / "staging" / f"{release_id}.partial-{os.getpid()}"
    temporary.mkdir(parents=True, mode=0o750)
    try:
        extract(sys.stdin.buffer, temporary)
        digest = verify(temporary)
        if not release_id.endswith(digest[:12]):
            raise ReceiverError("release id does not match manifest")
        (ROOT / "releases").mkdir(parents=True, exist_ok=True, mode=0o750)
        os.replace(temporary, destination)
        return {"status": "staged", "release_id": release_id,
                "manifest_sha256": digest}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def activate(release_id: str, expected: str) -> dict[str, object]:
    if not RELEASE_ID.fullmatch(release_id):
        raise ReceiverError("invalid release id")
    release = ROOT / "releases" / release_id
    digest = verify(release)
    if digest != expected or not release_id.endswith(digest[:12]):
        raise ReceiverError("release identity mismatch")
    current = ROOT / "current"
    previous_target = os.readlink(current) if current.is_symlink() else None
    if previous_target:
        previous_next = ROOT / "previous.next"
        if previous_next.is_symlink():
            previous_next.unlink()
        os.symlink(previous_target, previous_next)
        os.replace(previous_next, ROOT / "previous")
    current_next = ROOT / "current.next"
    if current_next.is_symlink():
        current_next.unlink()
    os.symlink(release.resolve(), current_next)
    os.replace(current_next, current)
    return {"status": "active", "release_id": release_id,
            "manifest_sha256": digest, "previous": previous_target}


def status() -> dict[str, object]:
    result: dict[str, object] = {}
    for name in ("current", "previous"):
        link = ROOT / name
        if not link.is_symlink():
            result[name] = None
            continue
        target = Path(os.readlink(link))
        result[name] = {"release_id": target.name,
                        "manifest_sha256": verify(target, allow_private_sample=True),
                        "private_sample": "preview" in target.name}
    return result


def main() -> int:
    try:
        command = shlex.split(os.environ.get("SSH_ORIGINAL_COMMAND", "status"))
        if command == ["status"]:
            result = status()
        elif len(command) == 2 and command[0] == "stage":
            result = stage(command[1])
        elif len(command) == 3 and command[0] in {"activate", "rollback"}:
            result = activate(command[1], command[2])
        else:
            raise ReceiverError("command is not permitted")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ReceiverError, OSError, tarfile.TarError, UnicodeError) as error:
        print(json.dumps({"status": "rejected", "detail": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
