from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .pipeline import LockHeldError, run, run_lock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Downconvert aged Radarr/Sonarr current-library video and hand it to the "
            "archive-movies/archive-tv roots. Defaults to a safe dry run: use --execute "
            "to actually transcode, move, and call the Radarr/Sonarr delete-file APIs."
        )
    )
    parser.add_argument("--config", type=Path, required=True, help="Path to config JSON")
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually transcode/move/delete. Without this flag, only lists candidates.",
    )
    parser.add_argument(
        "--max-files", type=int, default=None,
        help="Override the config's max_files_per_run for this invocation.",
    )
    parser.add_argument(
        "--library", choices=["movies", "tv", "both"], default="both",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = Config.load(args.config)
    max_files = args.max_files if args.max_files is not None else config.max_files_per_run
    dry_run = not args.execute

    try:
        with run_lock(config.lock_file):
            summary = run(config, dry_run=dry_run, max_files=max_files, library=args.library)
    except LockHeldError as exc:
        logging.error(str(exc))
        return 1

    mode = "DRY RUN" if dry_run else "EXECUTE"
    print(f"[{mode}] candidates found: {summary['total_candidates_found']}, "
          f"processed: {summary['processed']}, "
          f"succeeded: {summary['succeeded']}, failed: {summary['failed']}")
    print(f"Full log: {summary['log_file']}")
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
