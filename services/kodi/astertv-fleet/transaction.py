#!/usr/bin/env python3
"""Atomic directory promotion primitive with deterministic failure injection."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {path.relative_to(root).as_posix(): sha(path) for path in sorted(root.rglob("*")) if path.is_file()}


def promote(source: Path, target: Path, expected: dict[str, str], fail_at: str | None = None) -> dict:
    if inventory(source) != expected:
        raise ValueError("source-manifest-drift")
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}-stage-", dir=parent))
    previous = parent / f".{target.name}-previous"
    moved_previous = False
    try:
        shutil.rmtree(stage)
        shutil.copytree(source, stage)
        if fail_at == "after-stage":
            raise RuntimeError("synthetic-interruption-after-stage")
        if inventory(stage) != expected:
            raise ValueError("staged-manifest-drift")
        if previous.exists():
            shutil.rmtree(previous)
        if target.exists():
            os.replace(target, previous)
            moved_previous = True
        if fail_at == "after-predecessor-move":
            raise RuntimeError("synthetic-interruption-after-predecessor-move")
        os.replace(stage, target)
        if inventory(target) != expected:
            raise ValueError("promoted-manifest-drift")
        return {"outcome": "promoted", "files": len(expected), "rollback_available": moved_previous}
    except Exception:
        if moved_previous and previous.exists() and not target.exists():
            os.replace(previous, target)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def rollback(target: Path) -> dict:
    previous = target.parent / f".{target.name}-previous"
    if not previous.is_dir():
        raise ValueError("rollback-unavailable")
    failed = target.parent / f".{target.name}-failed"
    if failed.exists():
        shutil.rmtree(failed)
    if target.exists():
        os.replace(target, failed)
    try:
        os.replace(previous, target)
    except Exception:
        if failed.exists() and not target.exists():
            os.replace(failed, target)
        raise
    return {"outcome": "rolled-back", "files": len(inventory(target))}
