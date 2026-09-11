"""Operator CLI for status, run, verify, resume and rollback."""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
import tempfile
from pathlib import Path

from .collector import Collector
from .manifest import load_manifest, promote_candidates
from .mirror import build_mirror, package_hash, verify_mirror


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "resume", "status", "verify", "rollback",
                                         "mirror-build", "mirror-verify"))
    parser.add_argument("--wiki-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--mirror-root", type=Path)
    args = parser.parse_args()
    if args.mode in {"mirror-build", "mirror-verify"}:
        if args.mirror_root is None:
            parser.error("--mirror-root is required for mirror modes")
        if args.mode == "mirror-verify":
            print(json.dumps(verify_mirror(args.wiki_root, args.mirror_root), sort_keys=True))
            return 0
        temporary = Path(tempfile.mkdtemp(prefix="aster-mirror-double-"))
        try:
            first = temporary / "first"
            second = temporary / "second"
            one = build_mirror(args.wiki_root, first)
            two = build_mirror(args.wiki_root, second)
            if one != two or package_hash(first) != package_hash(second):
                raise RuntimeError("mirror double-build mismatch")
            result = build_mirror(args.wiki_root, args.mirror_root)
            result["verified_entries"] = verify_mirror(args.wiki_root, args.mirror_root)["checked"]
            print(json.dumps(result, sort_keys=True))
            return 0
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
    collector = Collector(args.wiki_root, args.state_root)
    if args.mode == "status":
        print(json.dumps({"schema_version": 1, "latest": collector.state.latest(),
                          "interrupted": collector.state.stale_running()}, sort_keys=True))
        return 0
    if args.mode == "verify":
        print(json.dumps(collector.verify(), sort_keys=True)); return 0
    if args.mode == "rollback":
        collector.rollback(); print('{"status":"rolled-back"}'); return 0
    manifest_path = args.wiki_root / "sources/sources.json"
    promote_candidates(args.state_root, manifest_path)
    manifest = load_manifest(manifest_path)
    run_id = args.run_id or ("run-" + secrets.token_hex(8))
    result = collector.run([source for source in manifest["sources"] if source["enabled"]], run_id)
    print(json.dumps(result, sort_keys=True))
    return 1 if result["failed"] or result["quarantined"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
