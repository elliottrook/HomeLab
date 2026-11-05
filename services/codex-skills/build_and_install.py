#!/usr/bin/env python3
"""Build a source manifest and optionally install the AsterTV Codex skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
SKILLS = ("astertv-fleet-engineer", "astertv-design-engineer")
IGNORED = {"__pycache__", ".DS_Store"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(skill: str) -> list[dict]:
    root = HERE / skill
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        safe = PurePosixPath(relative)
        if safe.is_absolute() or ".." in safe.parts:
            raise ValueError("unsafe-skill-path")
        rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha(path)})
    if not rows or rows[0]["path"] != "SKILL.md":
        raise ValueError(f"skill-entrypoint-missing:{skill}")
    return rows


def manifest() -> dict:
    return {"schema_version": 1, "kind": "codex-skill-source-manifest", "skills": [{"name": skill, "files": files(skill)} for skill in SKILLS]}


def canonical(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def install(target: Path, apply: bool) -> dict:
    source_manifest = manifest()
    target = target.resolve()
    result = {"target": str(target), "apply": apply, "skills": []}
    for item in source_manifest["skills"]:
        skill = item["name"]
        destination = target / skill
        if destination.exists():
            raise ValueError(f"skill-target-exists:{destination}")
        result["skills"].append({"name": skill, "files": len(item["files"]), "destination": str(destination)})
        if not apply:
            continue
        target.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{skill}-", dir=target))
        try:
            for row in item["files"]:
                source = HERE / skill / row["path"]
                if sha(source) != row["sha256"]:
                    raise ValueError(f"skill-source-drift:{skill}:{row['path']}")
                output = temporary / row["path"]
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output)
            for row in item["files"]:
                if sha(temporary / row["path"]) != row["sha256"]:
                    raise ValueError(f"skill-copy-drift:{skill}:{row['path']}")
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--write-manifest", type=Path)
    args = parser.parse_args(argv)
    if args.apply and args.target is None:
        parser.error("--apply requires --target")
    source_manifest = manifest()
    if args.write_manifest:
        args.write_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.write_manifest.write_text(canonical(source_manifest))
    if args.target:
        print(canonical(install(args.target, args.apply)), end="")
    else:
        print(canonical(source_manifest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
