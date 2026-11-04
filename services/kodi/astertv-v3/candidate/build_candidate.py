#!/usr/bin/env python3
"""Build and validate a reproducible, non-release Stream A page candidate."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[4]
V3 = ROOT / "services/kodi/astertv-v3"
V2 = ROOT / "services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz"
V2_SHA256 = "e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7"
PROFILE = Path("/Users/jelliott/Library/Application Support/Kodi")
PILOT = Path("/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app/Contents/Resources/Kodi/portable_data")
SOURCE_NAMES = (
    "README.md", "activate-mini-pilot.sh", "apply_art_title_focus.py",
    "apply_button_focus.py", "jellyfin_trailer_route.py", "pilot_jellyfin_trailer_smoke.py",
    "prepare-mini-pilot.sh", "run-mini-pilot.sh", "overlay", "patches", "pilot",
    "candidate/fixture-schema.json",
)
SECRET = re.compile(
    rb"(?i)(?:password|passwd|api[_ -]?key|access[_ -]?token|client[_ -]?secret)"
    rb"\s*[:=]\s*['\"][^'\"\r\n]{4,}"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError("unsafe-candidate-path")
    return path


def source_files() -> list[Path]:
    files = []
    for name in SOURCE_NAMES:
        path = V3 / name
        if path.is_symlink() or not path.exists():
            raise ValueError("candidate-source-missing-or-symlink:" + name)
        if path.is_file():
            files.append(path)
        else:
            for child in sorted(path.rglob("*")):
                if child.is_symlink():
                    raise ValueError("candidate-source-symlink:" + str(child))
                if child.is_file() and child.name not in (".DS_Store",) and "__pycache__" not in child.parts:
                    files.append(child)
    return sorted(set(files))


def profile_fingerprint(root: Path = PROFILE) -> dict:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("retained-profile-boundary-missing")
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("retained-profile-symlink")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            rows.append((relative, path.stat().st_size, sha256_file(path)))
    encoded = json.dumps(rows, separators=(",", ":")).encode()
    return {"files": len(rows), "sha256": sha256_bytes(encoded)}


def scan(files: list[Path]) -> None:
    for path in files:
        data = path.read_bytes()
        if b"-----BEGIN " in data and b"PRIVATE KEY-----" in data:
            raise ValueError("private-key-in-candidate:" + str(path))
        if SECRET.search(data):
            raise ValueError("credential-assignment-in-candidate:" + str(path))


def run_gates() -> list[dict]:
    commands = (
        (["python3", "test_shared_language.py"], V3),
        (["python3", "test_jellyfin_trailer_route.py"], V3),
        (["python3", "test_tv_details_package.py"], V3),
        (["python3", "test_reliability.py"], V3 / "reliability"),
        (["python3", "test_repair.py"], V3 / "deploy/news-playback"),
        (["python3", "test_candidate.py"], V3 / "candidate"),
    )
    results = []
    for command, cwd in commands:
        completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
        if completed.returncode:
            raise ValueError("candidate-gate-failed:" + command[-1] + "\n" + completed.stdout + completed.stderr)
        results.append({"command": " ".join(command), "outcome": "passed"})
    return results


def tar_bytes(files: list[Path], manifest: bytes, screenshots: list[Path]) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in files + screenshots:
                relative = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else "review/screenshots/" + path.name
                info = tarfile.TarInfo("astertv-v3-page-candidate/" + relative)
                data = path.read_bytes()
                info.size = len(data); info.mode = 0o644; info.mtime = 0; info.uid = 0; info.gid = 0
                archive.addfile(info, io.BytesIO(data))
            info = tarfile.TarInfo("astertv-v3-page-candidate/manifest.json")
            info.size = len(manifest); info.mode = 0o644; info.mtime = 0; info.uid = 0; info.gid = 0
            archive.addfile(info, io.BytesIO(manifest))
    return buffer.getvalue()


def validate_archive(data: bytes) -> dict:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            relative = member.name.removeprefix("astertv-v3-page-candidate/")
            safe_relative(relative)
            if not member.isfile():
                raise ValueError("non-file-candidate-member")
        manifest_member = archive.getmember("astertv-v3-page-candidate/manifest.json")
        manifest = json.load(archive.extractfile(manifest_member))
        by_name = {member.name: member for member in members}
        for row in manifest["inputs"]:
            name = "astertv-v3-page-candidate/" + row["path"]
            member = by_name[name]
            payload = archive.extractfile(member).read()
            if len(payload) != row["bytes"] or sha256_bytes(payload) != row["sha256"]:
                raise ValueError("candidate-member-drift:" + row["path"])
        return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--allow-pending-visual", action="store_true")
    args = parser.parse_args()
    if sha256_file(V2) != V2_SHA256:
        raise SystemExit("immutable-v2-baseline-drift")
    if not (PILOT / ".astertv-v3-portable").is_file() or PILOT == PROFILE:
        raise SystemExit("portable-pilot-boundary-failed")
    before = profile_fingerprint()
    files = source_files()
    scan(files)
    screenshots = sorted(args.screenshots.glob("*.png")) if args.screenshots and args.screenshots.is_dir() else []
    if not screenshots and not args.allow_pending_visual:
        raise SystemExit("physical-screenshots-required")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()
    gates = run_gates()
    inputs = [{"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
               "sha256": sha256_file(path)} for path in files]
    for image in screenshots:
        inputs.append({"path": "review/screenshots/" + image.name, "bytes": image.stat().st_size,
                       "sha256": sha256_file(image)})
    after = profile_fingerprint()
    if after != before:
        raise SystemExit("retained-profile-changed-during-build")
    manifest = {
        "schema": 1,
        "kind": "astertv-v3-stream-a-page-candidate",
        "release": False,
        "status": "visual-acceptance-pending" if not screenshots else "review-candidate",
        "commit": commit,
        "immutable_v2_sha256": V2_SHA256,
        "retained_profile": after,
        "portable_boundary": str(PILOT),
        "gates": gates,
        "inputs": inputs,
        "screenshots": [image.name for image in screenshots],
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    package = tar_bytes(files, encoded, screenshots)
    validate_archive(package)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name("." + args.output.name + ".tmp")
    temporary.write_bytes(package)
    os.replace(temporary, args.output)
    print(json.dumps({"output": str(args.output), "bytes": len(package),
                      "sha256": sha256_bytes(package), "status": manifest["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
