#!/usr/bin/env python3
"""Idempotently register Aster Games in the source-local Beszel hub."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import sqlite3
import string


NAME = "Aster Games"
HOST = "192.168.20.38"
PORT = "45876"
ALPHABET = string.ascii_lowercase + string.digits


def record_id() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(15))


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%fZ")


def register(connection: sqlite3.Connection, token_file: Path) -> dict:
    rows = connection.execute(
        "select id,name,host,port from systems where name=? or host=?", (NAME, HOST)
    ).fetchall()
    if len(rows) > 1:
        raise RuntimeError("beszel-system-conflict")

    if rows:
        system_id, name, host, port = rows[0]
        if (name, host, port) != (NAME, HOST, PORT):
            raise RuntimeError("beszel-system-identity-mismatch")
        fingerprints = connection.execute(
            "select token from fingerprints where system=?", (system_id,)
        ).fetchall()
        if len(fingerprints) != 1 or not fingerprints[0][0]:
            raise RuntimeError("beszel-fingerprint-missing")
        token = fingerprints[0][0]
        state = "existing"
    else:
        users = connection.execute(
            "select users from systems where json_array_length(users)>0 order by name limit 1"
        ).fetchone()
        if not users or not users[0]:
            raise RuntimeError("beszel-users-authority-missing")
        system_id = record_id()
        token = secrets.token_urlsafe(30)
        now = timestamp()
        connection.execute(
            "insert into systems(created,host,id,info,name,port,status,updated,users) "
            "values(?,?,?,?,?,?,?,?,?)",
            (now, HOST, system_id, None, NAME, PORT, "pending", now, users[0]),
        )
        connection.execute(
            "insert into fingerprints(fingerprint,id,system,token,updated) values(?,?,?,?,?)",
            ("", record_id(), system_id, token, now),
        )
        state = "created"

    token_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write("TOKEN=" + token + "\n")
    os.chmod(token_file, 0o600)
    return {"state": state, "system_id": system_id, "token_printed": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=Path("/opt/beszel/data/data.db"))
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    args = parser.parse_args(argv)

    args.checkpoint.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    source = sqlite3.connect(args.database)
    checkpoint = sqlite3.connect(args.checkpoint)
    source.backup(checkpoint)
    checkpoint.close()
    os.chmod(args.checkpoint, 0o600)
    try:
        source.execute("begin immediate")
        result = register(source, args.token_file)
        source.commit()
    except Exception:
        source.rollback()
        raise
    finally:
        source.close()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
