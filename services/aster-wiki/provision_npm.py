#!/usr/bin/env python3
"""Provision the Aster Wiki proxy host in Nginx Proxy Manager."""

import argparse
import datetime as dt
import json
import os
import sqlite3
from pathlib import Path


DOMAIN = "wiki.elliottrook.com"
TEMPLATE_DOMAIN = "proxy.elliottrook.com"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--prior-export", required=True, type=Path)
    args = parser.parse_args()

    database = sqlite3.connect(args.database)
    database.row_factory = sqlite3.Row

    args.backup.parent.mkdir(parents=True, exist_ok=True)
    backup = sqlite3.connect(args.backup)
    database.backup(backup)
    backup.close()
    os.chmod(args.backup, 0o600)

    template = database.execute(
        "SELECT * FROM proxy_host WHERE is_deleted = 0 AND domain_names = ?",
        (json.dumps([TEMPLATE_DOMAIN]),),
    ).fetchone()
    if template is None:
        raise SystemExit("known-good NPM proxy host template is missing")
    if template["certificate_id"] != 8:
        raise SystemExit("known-good wildcard certificate assignment changed")

    current = database.execute(
        "SELECT * FROM proxy_host WHERE is_deleted = 0 AND domain_names = ?",
        (json.dumps([DOMAIN]),),
    ).fetchone()
    args.prior_export.write_text(
        json.dumps(dict(current) if current else None, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(args.prior_export, 0o600)

    values = dict(template)
    values.update(
        {
            "domain_names": json.dumps([DOMAIN]),
            "forward_host": "192.168.20.34",
            "forward_port": 8787,
            "advanced_config": template["advanced_config"].replace(
                TEMPLATE_DOMAIN, DOMAIN
            ),
            "meta": json.dumps({"nginx_online": True, "nginx_err": None}),
            "modified_on": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "enabled": 1,
            "is_deleted": 0,
        }
    )

    if current:
        host_id = current["id"]
        editable = [key for key in values if key not in {"id", "created_on"}]
        database.execute(
            f"UPDATE proxy_host SET {', '.join(f'{key} = ?' for key in editable)} "
            "WHERE id = ?",
            [values[key] for key in editable] + [host_id],
        )
        action = "updated"
    else:
        values.pop("id")
        values["created_on"] = values["modified_on"]
        columns = list(values)
        database.execute(
            f"INSERT INTO proxy_host ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})",
            [values[key] for key in columns],
        )
        host_id = database.execute("SELECT last_insert_rowid()").fetchone()[0]
        action = "created"

    database.commit()
    result = database.execute(
        "SELECT id, domain_names, forward_scheme, forward_host, forward_port, "
        "certificate_id, ssl_forced, enabled FROM proxy_host WHERE id = ?",
        (host_id,),
    ).fetchone()
    print(json.dumps({"action": action, **dict(result)}, sort_keys=True))


if __name__ == "__main__":
    main()
