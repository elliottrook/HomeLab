#!/usr/bin/env python3
"""Queue a reviewed source batch and its explicitly named manual uploads."""

from __future__ import annotations

import argparse
from pathlib import Path

from aster_wiki.manifest import load_manifest, write_candidate, write_upload


def queue_batch(batch_path: Path, state_root: Path, upload_root: Path) -> dict[str, int]:
    manifest = load_manifest(batch_path)
    queued = 0
    uploads = 0
    for source in manifest["sources"]:
        if source["kind"] == "manual":
            filename = Path(source["boundary"]["value"]).name
            content = (upload_root / filename).read_bytes()
            write_upload(state_root, source, content)
            uploads += 1
        write_candidate(state_root, source)
        queued += 1
    return {"queued": queued, "uploads": uploads}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--upload-root", type=Path, required=True)
    args = parser.parse_args()
    result = queue_batch(args.batch, args.state_root, args.upload_root)
    print(f"queued={result['queued']} uploads={result['uploads']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
