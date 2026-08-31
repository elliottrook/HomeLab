from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .arr_client import ArrApiError, RadarrClient, SonarrClient
from .candidates import Candidate, find_episode_candidates, find_movie_candidates
from .config import Config
from .transcode import TranscodeError, compute_bitrate_plan, probe, transcode_2pass, verify_output

log = logging.getLogger("video_archiver.pipeline")


class LockHeldError(RuntimeError):
    pass


@contextmanager
def run_lock(lock_file: Path):
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise LockHeldError(
            f"Lock file {lock_file} already exists — a previous run may still be in progress "
            f"or exited uncleanly. Remove it manually only after confirming no run is active."
        )
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        lock_file.unlink(missing_ok=True)


class RunLogger:
    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.path = log_dir / f"run-{stamp}.jsonl"
        self._fh = open(self.path, "a", encoding="utf-8")

    def record(self, **fields) -> None:
        fields["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._fh.write(json.dumps(fields, default=str) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def _delete_source(candidate: Candidate, radarr: RadarrClient, sonarr: SonarrClient) -> None:
    if candidate.kind == "movie":
        radarr.delete_movie_file(candidate.arr_file_id)
    elif candidate.kind == "episode":
        sonarr.delete_episode_file(candidate.arr_file_id)
    else:
        raise ValueError(f"unknown candidate kind: {candidate.kind}")


def _process_one(candidate: Candidate, config: Config, dry_run: bool,
                  radarr: RadarrClient, sonarr: SonarrClient, run_log: RunLogger) -> bool:
    dst_tmp: Path | None = None
    try:
        probe_result = probe(candidate.source_path, config)
        plan = compute_bitrate_plan(probe_result, config)

        run_log.record(
            event="candidate",
            kind=candidate.kind,
            title=candidate.title,
            source_path=str(candidate.source_path),
            source_size_bytes=candidate.size_bytes,
            date_added=candidate.date_added.isoformat(),
            archive_dest_path=str(candidate.archive_dest_path),
            planned_video_kbps=plan.video_kbps,
            planned_resolution=f"{plan.max_width}x{plan.max_height}",
            below_quality_floor=plan.below_quality_floor,
            dry_run=dry_run,
        )

        if dry_run:
            return True

        dst_tmp = candidate.archive_dest_path.with_suffix(
            candidate.archive_dest_path.suffix + ".partial"
        )
        transcode_2pass(candidate.source_path, dst_tmp, plan, config)

        ok, reason = verify_output(dst_tmp, probe_result.duration_s, config)
        if not ok:
            run_log.record(
                event="verify_failed", kind=candidate.kind, title=candidate.title,
                reason=reason,
            )
            dst_tmp.unlink(missing_ok=True)
            return False

        candidate.archive_dest_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(dst_tmp, candidate.archive_dest_path)
        dst_tmp = None  # renamed away; nothing left to clean up

        new_size = candidate.archive_dest_path.stat().st_size
        _delete_source(candidate, radarr, sonarr)

        run_log.record(
            event="archived",
            kind=candidate.kind,
            title=candidate.title,
            source_path=str(candidate.source_path),
            archive_dest_path=str(candidate.archive_dest_path),
            source_size_bytes=candidate.size_bytes,
            archive_size_bytes=new_size,
            reduction_fraction=(
                1 - (new_size / candidate.size_bytes) if candidate.size_bytes else None
            ),
        )
        return True

    except (TranscodeError, ArrApiError, OSError) as exc:
        run_log.record(
            event="error", kind=candidate.kind, title=candidate.title,
            source_path=str(candidate.source_path), error=str(exc),
        )
        log.error("failed to process %s: %s", candidate.title, exc)
        return False
    finally:
        if dst_tmp is not None:
            dst_tmp.unlink(missing_ok=True)


def run(config: Config, dry_run: bool, max_files: int, library: str) -> dict:
    radarr = RadarrClient(config.radarr_url, config.radarr_api_key)
    sonarr = SonarrClient(config.sonarr_url, config.sonarr_api_key)
    run_log = RunLogger(config.log_dir)

    candidates: list[Candidate] = []
    if library in ("movies", "both"):
        candidates += find_movie_candidates(radarr, config)
    if library in ("tv", "both"):
        candidates += find_episode_candidates(sonarr, config)

    candidates.sort(key=lambda c: c.date_added)  # oldest first
    batch = candidates[:max_files] if not dry_run else candidates

    succeeded = failed = 0
    for candidate in batch:
        ok = _process_one(candidate, config, dry_run, radarr, sonarr, run_log)
        succeeded += int(ok)
        failed += int(not ok)
        if not dry_run:
            time.sleep(1)  # small gap between heavy encode jobs

    summary = {
        "dry_run": dry_run,
        "total_candidates_found": len(candidates),
        "processed": len(batch),
        "succeeded": succeeded,
        "failed": failed,
        "log_file": str(run_log.path),
    }
    run_log.record(event="summary", **summary)
    run_log.close()
    return summary
