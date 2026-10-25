#!/usr/bin/env python3
"""Validate and synchronize Aster's four canonical UI sound masters."""

from __future__ import annotations

import hashlib
import shutil
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"
MOVEMENT_ALIASES = ("nav-left.wav", "nav-right.wav", "nav-up.wav", "nav-down.wav")
EXPECTED_SHA256 = {
    "movement": "227b863d35a6c6ea67df559b4d302706af669c6eee5ba86a47382164fdf3f0c8",
    "boundary": "57f108306b772252095811c9827dd6667c58f53e9c80f7f733976467057de6f6",
    "select": "a95d8c2a2d874a0f04b5ab82fb11d0a7a1d850562849de3c86cbf1050edb2910",
    "back": "33b9852ee00869cefd0040ce6a65573ec1a5606a87352917e7654d7b36348a54",
}
CANONICAL_FILES = {
    "movement": "nav-left.wav",
    "boundary": "notify.wav",
    "select": "select.wav",
    "back": "back.wav",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_master(kind: str, path: Path) -> None:
    with wave.open(str(path), "rb") as source:
        if source.getparams()[:3] != (2, 3, 48_000):
            raise RuntimeError(f"wrong audio format: {path.name}")
        if source.getnframes() / source.getframerate() >= 0.5:
            raise RuntimeError(f"sound is too long: {path.name}")
    actual = sha256(path)
    if actual != EXPECTED_SHA256[kind]:
        raise RuntimeError(f"canonical {kind} master drift: {path.name}")


def main() -> None:
    masters = {kind: RESOURCES / name for kind, name in CANONICAL_FILES.items()}
    for kind, path in masters.items():
        validate_master(kind, path)

    movement = masters["movement"]
    for name in MOVEMENT_ALIASES[1:]:
        shutil.copyfile(movement, RESOURCES / name)
    shutil.copyfile(
        ROOT.parent / "skin.asterhome" / "media" / "aster-icon-128.png",
        ROOT / "icon.png",
    )

    if any(sha256(RESOURCES / name) != EXPECTED_SHA256["movement"]
           for name in MOVEMENT_ALIASES):
        raise RuntimeError("movement aliases did not synchronize")
    print("Aster canonical UI sounds verified: movement, boundary, select, back")


if __name__ == "__main__":
    main()
