#!/usr/bin/env python3
"""Read-only filesystem/database preflight for the bounded M1 Stage 1 release.

This does not stop services, migrate a database, expire a request or authorize
installation. Live use also requires the separately documented quiescence gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path

INSTALL_FILES = {"broker_core.py", "broker_service.py"}
LIVE_FILES = INSTALL_FILES | {"broker_approval_service.py"}


class PreflightFailed(RuntimeError):
    pass


def check(release: Path, live_root: Path, now: int | None = None):
    manifest = json.loads((release / "manifest.json").read_text())
    if manifest.get("target_guest") != 104 or manifest.get("stage") != 1:
        raise PreflightFailed("wrong release target")
    if set(manifest.get("install_files", [])) != INSTALL_FILES:
        raise PreflightFailed("install scope differs from two-file release")
    if set(manifest.get("expected_live", {})) != LIVE_FILES:
        raise PreflightFailed("incomplete live baseline")
    if set(manifest.get("restart_services", [])) != {"homelab-broker.service", "homelab-broker-approval.service"}:
        raise PreflightFailed("restart scope differs from approved plan")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or name in {"", ".", ".."}:
            raise PreflightFailed("unsafe release member")
        member = release / name
        if member.is_symlink() or hashlib.sha256(member.read_bytes()).hexdigest() != expected:
            raise PreflightFailed("release content mismatch: " + name)
    if not INSTALL_FILES <= set(manifest["files"]):
        raise PreflightFailed("missing install artifact")
    for name, expected in manifest["expected_live"].items():
        member = live_root / "opt/homelab-broker" / name
        if member.is_symlink() or hashlib.sha256(member.read_bytes()).hexdigest() != expected:
            raise PreflightFailed("live baseline changed: " + name)
    database = live_root / "var/lib/homelab-broker/broker.db"
    if database.is_symlink():
        raise PreflightFailed("unexpected database symlink")
    observed = int(time.time()) if now is None else now
    # Read-only SQLite includes committed WAL state. Never use immutable=1 on a
    # running database, and never construct BrokerStore here (it migrates).
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise PreflightFailed("database integrity failed")
        active = connection.execute(
            "SELECT COUNT(*) FROM requests WHERE status IN ('pending','approved') AND expires_at>?",
            (observed,),
        ).fetchone()[0]
        expired_open = connection.execute(
            "SELECT COUNT(*) FROM requests WHERE status IN ('pending','approved') AND expires_at<=?",
            (observed,),
        ).fetchone()[0]
        if active:
            raise PreflightFailed("unexpired authorizations remain: " + str(active))
    finally:
        connection.close()
    return {"result": "passed", "observed_unix": observed, "unexpired_authorizations": active,
            "expired_open_rows_unchanged": expired_open, "integrity": integrity,
            "scope": "read-only; service quiescence and deployment approval still required"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--live-root", type=Path, default=Path("/"))
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.release, args.live_root), sort_keys=True))
    except (PreflightFailed, OSError, ValueError, KeyError, sqlite3.Error) as error:
        # No raw database/connection output or payload is included.
        print(json.dumps({"result": "blocked", "error_type": type(error).__name__,
                          "reason": str(error) if isinstance(error, PreflightFailed) else "preflight input or database unavailable"}))
        raise SystemExit(1)
