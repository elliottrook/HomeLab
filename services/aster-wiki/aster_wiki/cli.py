"""Operator CLI for status, run, verify, resume and rollback."""

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path

from .collector import Collector
from .manifest import load_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "resume", "status", "verify", "rollback"))
    parser.add_argument("--wiki-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    collector = Collector(args.wiki_root, args.state_root)
    if args.mode == "status":
        print(json.dumps({"schema_version": 1, "latest": collector.state.latest(),
                          "interrupted": collector.state.stale_running()}, sort_keys=True))
        return 0
    if args.mode == "verify":
        print(json.dumps(collector.verify(), sort_keys=True)); return 0
    if args.mode == "rollback":
        collector.rollback(); print('{"status":"rolled-back"}'); return 0
    manifest = load_manifest(args.wiki_root / "sources/sources.json")
    run_id = args.run_id or ("run-" + secrets.token_hex(8))
    result = collector.run([source for source in manifest["sources"] if source["enabled"]], run_id)
    print(json.dumps(result, sort_keys=True))
    return 1 if result["failed"] or result["quarantined"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
