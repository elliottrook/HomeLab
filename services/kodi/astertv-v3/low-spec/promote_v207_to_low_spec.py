#!/usr/bin/env python3
"""Install the immutable AsterTV v2.0.7 baseline on AsterTV-Jen only."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path


PACKAGE = Path(
    "/storage/.aster-staging/astertv-v2.0.7-release-2026-10-31/aster-v2-package"
)
PROMOTER = PACKAGE / "reconciliation/promote_v207_to_production.py"
EXPECTED_PROMOTER_SHA256 = (
    "116689a3f2dfc3e0b7880bf82eb0689306a81b4cd98a2ebf57f8fefa2525c987"
)
TARGET_HOST = "AsterTV-Jen"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if os.uname().nodename != TARGET_HOST:
        raise RuntimeError("AsterTV-Jen host only")
    if not PROMOTER.is_file() or sha256(PROMOTER) != EXPECTED_PROMOTER_SHA256:
        raise RuntimeError("unexpected v2.0.7 promoter")
    spec = importlib.util.spec_from_file_location("astertv_v207_promoter", PROMOTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load v2.0.7 promoter")
    promoter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(promoter)
    promoter.TARGETS = {TARGET_HOST: ("low-spec", False)}
    promoter.main()


if __name__ == "__main__":
    main()
