"""Idempotently provision tcf.elliottrook.com in Nginx Proxy Manager."""

import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path

DOMAIN = "tcf.elliottrook.com"
TEMPLATE_DOMAIN = "wiki.elliottrook.com"

parser = argparse.ArgumentParser()
parser.add_argument("--database", required=True, type=Path)
parser.add_argument("--backup", required=True, type=Path)
args = parser.parse_args()
database = sqlite3.connect(args.database)
database.row_factory = sqlite3.Row
backup = sqlite3.connect(args.backup)
database.backup(backup)
backup.close()
args.backup.chmod(0o600)
template = database.execute(
    "SELECT * FROM proxy_host WHERE is_deleted=0 AND domain_names=?",
    (json.dumps([TEMPLATE_DOMAIN]),),
).fetchone()
if template is None:
    raise SystemExit("known-good Authentik-protected wiki template missing")
current = database.execute(
    "SELECT * FROM proxy_host WHERE is_deleted=0 AND domain_names=?",
    (json.dumps([DOMAIN]),),
).fetchone()
advanced_config = template["advanced_config"].replace(TEMPLATE_DOMAIN, DOMAIN)
if "client_max_body_size 29m;" not in advanced_config:
    advanced_config = "client_max_body_size 29m;\n\n" + advanced_config
values = dict(template)
values.update({"domain_names": json.dumps([DOMAIN]), "forward_host": "192.168.20.35",
               "forward_port": 8080,
               "advanced_config": advanced_config,
               "meta": json.dumps({"nginx_online": True, "nginx_err": None}),
               "modified_on": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
               "enabled": 1, "is_deleted": 0})
if current:
    host_id = current["id"]
    editable = [key for key in values if key not in {"id", "created_on"}]
    database.execute(f"UPDATE proxy_host SET {', '.join(key+'=?' for key in editable)} WHERE id=?",
                     [values[key] for key in editable] + [host_id])
else:
    values.pop("id")
    values["created_on"] = values["modified_on"]
    columns = list(values)
    database.execute(f"INSERT INTO proxy_host ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                     [values[key] for key in columns])
    host_id = database.execute("SELECT last_insert_rowid()").fetchone()[0]
database.commit()
print({"id": host_id, "domain": DOMAIN, "backend": "192.168.20.35:8080"})
