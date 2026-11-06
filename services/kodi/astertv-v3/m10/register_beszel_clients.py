#!/usr/bin/env python3
"""Transactionally register exact AsterTV systems in Beszel without printing tokens."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import sqlite3
import string

TARGETS = {
    "astertv-bedroom": {"name": "AsterTV Bedroom", "host": "192.168.1.140"},
    "astertv-family": {"name": "AsterTV Family", "host": "192.168.1.157"},
    "astertv-jen": {"name": "AsterTV Jen", "host": "192.168.1.180"},
}
ALPHABET = string.ascii_lowercase + string.digits


def record_id() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(15))


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%fZ")


def register(connection: sqlite3.Connection, targets: dict, users: str,
             token_dir: Path) -> dict:
    token_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(token_dir, 0o700)
    result = {}
    for device, expected in targets.items():
        rows = connection.execute(
            "select id,name,host,port from systems where name=? or host=?",
            (expected["name"], expected["host"]),
        ).fetchall()
        if len(rows) > 1:
            raise RuntimeError(f"beszel-system-conflict:{device}")
        if rows:
            system_id, name, host, port = rows[0]
            if (name, host, port) != (expected["name"], expected["host"], "45876"):
                raise RuntimeError(f"beszel-system-identity-mismatch:{device}")
            fingerprint = connection.execute(
                "select token from fingerprints where system=?", (system_id,)
            ).fetchall()
            if len(fingerprint) != 1 or not fingerprint[0][0]:
                raise RuntimeError(f"beszel-fingerprint-missing:{device}")
            token = fingerprint[0][0]
            state = "existing"
        else:
            system_id = record_id()
            fingerprint_id = record_id()
            token = secrets.token_urlsafe(30)
            now = timestamp()
            connection.execute(
                "insert into systems(created,host,id,info,name,port,status,updated,users) "
                "values(?,?,?,?,?,?,?,?,?)",
                (now, expected["host"], system_id, None, expected["name"],
                 "45876", "pending", now, users),
            )
            connection.execute(
                "insert into fingerprints(fingerprint,id,system,token,updated) "
                "values(?,?,?,?,?)", ("", fingerprint_id, system_id, token, now)
            )
            state = "created"
        token_path = token_dir / f"{device}.env"
        descriptor = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write("TOKEN=" + token + "\n")
        os.chmod(token_path, 0o600)
        result[device] = {"state": state, "system_id": system_id}
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=Path("/opt/beszel/data/data.db"))
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--token-dir", type=Path,
                        default=Path("/run/astertv-beszel-enrollment"))
    args = parser.parse_args(argv)
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    source = sqlite3.connect(args.database)
    backup = sqlite3.connect(args.checkpoint)
    source.backup(backup)
    backup.close()
    os.chmod(args.checkpoint, 0o600)
    users = source.execute(
        "select users from systems where json_array_length(users)>0 order by name limit 1"
    ).fetchone()
    if not users or not users[0]:
        raise RuntimeError("beszel-users-authority-missing")
    try:
        source.execute("begin immediate")
        result = register(source, TARGETS, users[0], args.token_dir)
        source.commit()
    except Exception:
        source.rollback()
        raise
    finally:
        source.close()
    print(json.dumps({"systems": {key: value["state"] for key, value in result.items()},
                      "tokens_printed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
