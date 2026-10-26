#!/usr/bin/env python3
"""Verify that an F6 card pins the complete current V3/M3 packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_requirements(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "aster.stream-a.f6-current-packet-requirements.v1":
        raise ValueError("unsupported requirements schema")
    return data


def verify_card(card: str, requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, digest in requirements["host_paths"].items():
        if path not in card:
            failures.append(f"missing host path: {path}")
        if digest not in card:
            failures.append(f"missing host digest: {path}")
    for name, digest in requirements["m3_identities"].items():
        if digest not in card:
            failures.append(f"missing M3 identity: {name}")
    for digest in requirements["forbidden_superseded_hashes"]:
        if digest in card:
            failures.append(f"superseded digest present: {digest}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("card", type=Path)
    parser.add_argument("--requirements", type=Path, required=True)
    args = parser.parse_args()
    failures = verify_card(
        args.card.read_text(encoding="utf-8"), load_requirements(args.requirements)
    )
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print("F6 current-packet card: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
