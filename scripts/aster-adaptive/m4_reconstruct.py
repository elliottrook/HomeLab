"""Reconstruct one pinned synthetic evidence export in an isolated directory.

This copies only hash-pinned inputs, invokes the offline verifier, and returns a
content-free summary.  It does not execute the measurement runner or grant
review, deployment, or promotion authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


SCHEMA = "aster-m4-reconstruction-manifest.v1"
HEX = set("0123456789abcdef")


def _digest(path: Path) -> str:
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    return "sha256:" + value


def _relative(value: object) -> Path:
    if not isinstance(value, str):
        raise ValueError("manifest path must be a string")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError("manifest path must be repository-relative")
    return Path(*path.parts)


def _sha(value: object) -> bool:
    return (
        isinstance(value, str) and value.startswith("sha256:")
        and len(value) == 71 and set(value[7:]) <= HEX
    )


def load_manifest(path: Path) -> dict:
    value = json.loads(path.read_bytes(), object_pairs_hook=_unique)
    required = {
        "schema", "data_class", "evidence_path", "expected_head",
        "files", "expected", "runtime", "authority",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("reconstruction manifest fields differ")
    if value["schema"] != SCHEMA or value["data_class"] != "synthetic":
        raise ValueError("unsupported reconstruction manifest")
    if value["authority"] != "not-granted" or not _sha(value["expected_head"]):
        raise ValueError("manifest authority or checkpoint differs")
    _relative(value["evidence_path"])
    files = value["files"]
    if not isinstance(files, dict) or not files:
        raise ValueError("manifest files are required")
    for name, digest in files.items():
        _relative(name)
        if not _sha(digest):
            raise ValueError("manifest file digest differs")
    if value["evidence_path"] not in files:
        raise ValueError("evidence export is not hash-pinned")
    if not isinstance(value["expected"], dict) or set(value["expected"]) != {
        "event_count", "measurement_authenticity", "review_approval",
    }:
        raise ValueError("expected reconstruction result differs")
    if not isinstance(value["runtime"], dict) or set(value["runtime"]) != {
        "python", "pydantic",
    }:
        raise ValueError("runtime pin differs")
    return value


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def reconstruct(repository: Path, manifest_path: Path) -> dict:
    repository = repository.resolve()
    manifest = load_manifest(manifest_path)
    try:
        import pydantic
    except ImportError as error:
        raise ValueError("pinned reconstruction runtime is unavailable") from error
    actual_runtime = {
        "python": ".".join(map(str, sys.version_info[:3])),
        "pydantic": pydantic.__version__,
    }
    if actual_runtime != manifest["runtime"]:
        raise ValueError("reconstruction runtime differs from manifest")
    with tempfile.TemporaryDirectory(prefix="aster-m4-restore-") as directory:
        isolated = Path(directory)
        for name, expected_digest in manifest["files"].items():
            relative = _relative(name)
            source = repository / relative
            mode = source.lstat().st_mode
            if not stat.S_ISREG(mode) or source.is_symlink():
                raise ValueError("manifest source must be a regular file")
            if _digest(source) != expected_digest:
                raise ValueError(f"manifest digest mismatch: {name}")
            destination = isolated / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        verifier = isolated / "scripts/aster-adaptive/verify_evidence.py"
        evidence = isolated / _relative(manifest["evidence_path"])
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
        }
        completed = subprocess.run(
            [sys.executable, str(verifier), str(evidence),
             "--expected-head", manifest["expected_head"]],
            cwd=isolated, env=environment, text=True, capture_output=True,
            timeout=30, check=False,
        )
        if completed.returncode != 0:
            raise ValueError("isolated evidence reconstruction failed")
        result = json.loads(completed.stdout, object_pairs_hook=_unique)
        for key, expected in manifest["expected"].items():
            if result.get(key) != expected:
                raise ValueError(f"reconstruction result differs: {key}")
        if result.get("verified_head") != manifest["expected_head"]:
            raise ValueError("reconstruction head differs")
        if len(result.get("evaluations", [])) != 1:
            raise ValueError("reconstruction evaluation count differs")
        return {
            "schema": "aster-m4-reconstruction-result.v1",
            "status": "complete", "event_count": result["event_count"],
            "verified_head": result["verified_head"],
            "evidence_sha256": manifest["files"][manifest["evidence_path"]],
            "measurement_authenticity": result["measurement_authenticity"],
            "review_approval": result["review_approval"],
            "authority": "not-granted",
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(reconstruct(args.repository, args.manifest),
                     sort_keys=True, separators=(",", ":")))
