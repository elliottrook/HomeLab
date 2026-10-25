#!/usr/bin/env python3
"""Validate Aster's canonical startup and mouse-click UI sound masters."""

from __future__ import annotations

import hashlib
import shutil
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"
EXPECTED_SHA256 = {
    "nav-left.wav": "233b96079ed5471e774b86f840f7ef00dabe2b6f5c5effe91d4ccb17aafb2285",
    "nav-right.wav": "dce25cc207715fba406fb86905e32c4bfbfc5ec17be83abff2db2d9cb77aaa28",
    "nav-up.wav": "08037d2c1e0dd6f930715584493f98e09885e3a8126df076a3cdf01729663cba",
    "nav-down.wav": "6c414975aff7b7d4caa8866a0e4ffa41f80f222b1c4ca5db199a45c34d741ea9",
    "notify.wav": "c093d94abbabc0383d278b9f8e39dda8ca5fbfdee8080bdce1c4078126e175c8",
    "select.wav": "6e38a7c6fc9964c8c53e49409df42d53200ce51e221c2dbb63b13a8bdb811c3f",
    "back.wav": "b5c3678e2849cb6b9dd15125f2e1ebeb9afda6f469524d6bada3a20ba6424125",
    "startup.wav": "f41cc896c664e234986330799bc3b75c460ab6eb87c3883df338b0353a06b7e2",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_master(path: Path) -> None:
    with wave.open(str(path), "rb") as source:
        if source.getparams()[:3] != (2, 3, 48_000):
            raise RuntimeError(f"wrong audio format: {path.name}")
        limit = 4.0 if path.name == "startup.wav" else 0.6
        if source.getnframes() / source.getframerate() >= limit:
            raise RuntimeError(f"sound is too long: {path.name}")
    actual = sha256(path)
    if actual != EXPECTED_SHA256[path.name]:
        raise RuntimeError(f"canonical master drift: {path.name}")


def main() -> None:
    for name in EXPECTED_SHA256:
        validate_master(RESOURCES / name)
    shutil.copyfile(
        ROOT.parent / "skin.asterhome" / "media" / "aster-icon-128.png",
        ROOT / "icon.png",
    )
    print("Aster canonical UI sounds verified: startup plus seven click cues")


if __name__ == "__main__":
    main()
