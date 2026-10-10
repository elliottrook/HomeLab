"""Idempotently add the private Content Desk hostname to Pi-hole v6."""

import argparse
import os
import shutil
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--config", type=Path, required=True)
parser.add_argument("--backup", type=Path, required=True)
args = parser.parse_args()

text = args.config.read_text(encoding="utf-8")
entry = '    "192.168.50.23 tcf.elliottrook.com",'
if "tcf.elliottrook.com" not in text:
    if args.backup.exists():
        raise RuntimeError(f"refusing to replace backup: {args.backup}")
    shutil.copy2(args.config, args.backup)
    os.chmod(args.backup, 0o600)
    anchor = '    "192.168.50.23 wiki.elliottrook.com",'
    if text.count(anchor) != 1:
        raise RuntimeError("expected unique wiki dns.hosts anchor is missing")
    temporary = args.config.with_name(args.config.name + ".tcf.tmp")
    temporary.write_text(text.replace(anchor, anchor + "\n" + entry), encoding="utf-8")
    os.chmod(temporary, args.config.stat().st_mode & 0o777)
    temporary.replace(args.config)
print("tcf-private-dns=present")
