#!/usr/bin/env python3
"""Metadata-only health check for the pull-based Forgejo bundle runner."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import stat
import time
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def _policy(path: Path, pattern: re.Pattern[str], label: str) -> str:
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022:
        raise ValueError(f"{label} policy permissions are unsafe")
    value = path.read_text(encoding="ascii").strip()
    if not pattern.fullmatch(value):
        raise ValueError(f"{label} policy is invalid")
    return value


def check(ledger_path: Path, base_file: Path, policy_file: Path, signers: Path,
          *, now: int, max_success_age: int) -> dict[str, object]:
    base = _policy(base_file, GIT_SHA, "base revision")
    policy = _policy(policy_file, SHA256, "policy digest")
    signer_info = signers.stat()
    if not stat.S_ISREG(signer_info.st_mode) or signer_info.st_mode & 0o022:
        raise ValueError("allowed-signers permissions are unsafe")
    signer_count = sum(1 for line in signers.read_text(encoding="ascii").splitlines() if line.strip())
    if signer_count != 1:
        raise ValueError("allowed-signers must contain exactly one principal")
    connection = sqlite3.connect(f"file:{ledger_path}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError("ledger integrity check failed")
        counts = dict(connection.execute(
            "SELECT state,COUNT(*) FROM requests GROUP BY state"
        ).fetchall())
        last_consumed = connection.execute(
            "SELECT MAX(updated_at) FROM requests WHERE state='consumed'"
        ).fetchone()[0]
    finally:
        connection.close()
    age = None if last_consumed is None else max(0, now - int(last_consumed))
    if age is None or age > max_success_age:
        raise ValueError("last successful consume is stale or absent")
    return {
        "status": "healthy", "base_revision": base,
        "policy_digest": policy, "signer_principals": signer_count,
        "ledger_integrity": integrity, "states": counts,
        "last_consumed_at": int(last_consumed), "last_success_age_seconds": age,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--base-file", type=Path, required=True)
    parser.add_argument("--policy-file", type=Path, required=True)
    parser.add_argument("--allowed-signers", type=Path, required=True)
    parser.add_argument("--max-success-age", type=int, default=604800)
    args = parser.parse_args()
    try:
        result = check(
            args.ledger, args.base_file, args.policy_file, args.allowed_signers,
            now=int(time.time()), max_success_age=args.max_success_age,
        )
    except (OSError, UnicodeError, sqlite3.Error, ValueError) as exc:
        raise SystemExit(f"UNHEALTHY {exc}") from None
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
