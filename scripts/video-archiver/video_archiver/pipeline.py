from __future__ import annotations

import json
import logging
import os
import shutil
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .arr_client import ArrApiError, RadarrClient, SonarrClient
from .candidates import Candidate, find_episode_candidates, find_movie_candidates
from .config import Config
from .jellyfin_client import JellyfinApiError, JellyfinClient
from .transcode import TranscodeError, compute_bitrate_plan, probe, transcode, verify_output

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
    # Deleting the file alone is not enough: confirmed by live testing (2026-09-07) that
    # Radarr/Sonarr leave the parent movie/episode monitored with hasFile=false afterward,
    # which risks an automatic re-search/re-download of the file just archived. Unmonitor
    # is called right after delete, using the same candidate — a failure here still
    # surfaces as this candidate failing overall (existing exception handling in
    # _process_one), which is the right call: the archived copy already exists safely on
    # disk either way, but a missed unmonitor is a real re-download risk that needs an
    # operator's attention, not a silently-swallowed warning.
    if candidate.kind == "movie":
        radarr.delete_movie_file(candidate.arr_file_id)
        radarr.unmonitor_movie(candidate.arr_parent_id)
    elif candidate.kind == "episode":
        sonarr.delete_episode_file(candidate.arr_file_id)
        sonarr.unmonitor_episode(candidate.arr_parent_id)
    else:
        raise ValueError(f"unknown candidate kind: {candidate.kind}")


def _cleanup_leftovers(candidate: Candidate, config: Config) -> None:
    """Radarr/Sonarr's delete-file API only removes the video file itself — it leaves
    behind Jellyfin's own per-file ".trickplay" thumbnail-preview cache folder. Confirmed
    by live testing (2026-09-07): that leftover folder was enough for Jellyfin's scanner
    to keep showing an empty series entry in the main current-library Shows/Movies
    listing after every real file had already been archived away. Remove that cache
    folder, then remove any directories left empty above it, up to (but never including)
    the configured current-library root. Best-effort: failures here are logged but don't
    fail the candidate — the archive+delete already succeeded by the time this runs."""
    trickplay_dir = candidate.source_path.parent / (candidate.source_path.stem + ".trickplay")
    if trickplay_dir.is_dir():
        shutil.rmtree(trickplay_dir, ignore_errors=True)

    current_root = (
        config.movies_current_root if candidate.kind == "movie" else config.tv_current_root
    )
    directory = candidate.source_path.parent
    while directory != current_root and current_root in directory.parents:
        try:
            if any(directory.iterdir()):
                break
            directory.rmdir()
        except OSError:
            break
        directory = directory.parent


def _process_one(candidate: Candidate, config: Config, dry_run: bool,
                  radarr: RadarrClient, sonarr: SonarrClient, run_log: RunLogger) -> bool:
    # Dry run reports candidate metadata straight from the arr APIs only — it deliberately
    # never calls ffprobe, so it can run before ffmpeg/ffprobe are installed on the host
    # (Video Library Archiving project doc, Milestone 1 gate).
    if dry_run:
        try:
            run_log.record(
                event="candidate",
                kind=candidate.kind,
                title=candidate.title,
                source_path=str(candidate.source_path),
                source_size_bytes=candidate.size_bytes,
                date_added=candidate.date_added.isoformat(),
                archive_dest_path=str(candidate.archive_dest_path),
                dry_run=dry_run,
            )
            return True
        except OSError as exc:
            log.error("failed to log candidate %s: %s", candidate.title, exc)
            return False

    dst_tmp: Path | None = None
    try:
        # A raw disc image isn't a video container ffprobe can read directly --
        # confirmed for real 2026-09-11 (Rango, a UHD BluRay .iso): probe() fails
        # immediately with an opaque "Invalid data found when processing input",
        # giving no hint of the actual cause. Fail with a clear, specific reason
        # instead, so the Lab Doctor notification says exactly what's needed
        # (mount the ISO, extract the main feature .m2ts, re-tag and retry) rather
        # than a cryptic ffprobe error that needs a log dive to understand. This
        # tool deliberately doesn't automate ISO extraction itself -- picking the
        # right title out of a disc image (vs. trailers/extras/alternate angles)
        # needs a human looking at durations, not a guess.
        if candidate.source_path.suffix.lower() == ".iso":
            raise TranscodeError(
                "ISO file - manual processing needed: mount and extract the main feature "
                "(largest file under BDMV/STREAM/, confirm via ffprobe duration matching the "
                "movie's real runtime), then archive that file manually. See "
                "Video-Library-Archiving.md's ISO handling note for the full process."
            )

        probe_result = probe(candidate.source_path, config)

        # Stage the in-progress output in work_dir, NOT inside the archive tree.
        # Confirmed by live testing (2026-09-07): Jellyfin's real-time library monitor
        # watches the archive-tv/archive-movies folders and indexed a ".partial.mkv" file
        # while it was still being written, recording that filename in its database. Once
        # the finished file was atomically renamed away, Jellyfin's entry pointed at a path
        # that no longer existed — "Could not find file" on every playback attempt.
        # work_dir sits outside every Jellyfin library, so nothing there gets indexed; the
        # only write Jellyfin ever sees in the archive tree is the final atomic rename.
        # Must end in a real extension (.mkv), not .partial — ffmpeg's muxer picks the
        # output format from the filename extension, and ".partial" isn't recognized.
        config.work_dir.mkdir(parents=True, exist_ok=True)
        dst_tmp = config.work_dir / (
            candidate.archive_dest_path.stem + ".partial" + candidate.archive_dest_path.suffix
        )

        # Already at or under the target — re-encoding could only make it bigger.
        # Confirmed by live testing (2026-09-07): a source already using a low-bitrate
        # x265 encode nearly quintupled in size (0.29 GB -> 1.43 GB) when re-encoded at
        # this project's target bitrate. Relocate it as-is instead of transcoding.
        already_small_enough = candidate.size_bytes <= config.target_size_max_bytes
        if already_small_enough:
            shutil.copy2(candidate.source_path, dst_tmp)
            plan = None
        else:
            plan = compute_bitrate_plan(probe_result, config)
            transcode(candidate.source_path, dst_tmp, plan, config)

        run_log.record(
            event="candidate",
            kind=candidate.kind,
            title=candidate.title,
            source_path=str(candidate.source_path),
            source_size_bytes=candidate.size_bytes,
            date_added=candidate.date_added.isoformat(),
            archive_dest_path=str(candidate.archive_dest_path),
            already_small_enough=already_small_enough,
            planned_video_kbps=plan.video_kbps if plan else None,
            planned_resolution=f"{plan.max_width}x{plan.max_height}" if plan else None,
            below_quality_floor=plan.below_quality_floor if plan else None,
            dropped_audio_track_count=plan.dropped_audio_track_count if plan else None,
            kept_english_subtitle_count=len(plan.english_subtitle_indices) if plan else None,
            dry_run=dry_run,
        )

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

        try:
            _cleanup_leftovers(candidate, config)
        except OSError as exc:
            # Best-effort tidy-up; the archive+delete already succeeded, so this
            # candidate still counts as a success — just log it for follow-up.
            log.warning("leftover cleanup failed for %s: %s", candidate.title, exc)

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

    # One rescan at the end of the batch, not per-file: confirmed necessary by live
    # testing (2026-09-07) — without it, Jellyfin's own database keeps stale state (an
    # in-progress temp filename it indexed mid-encode, or an empty current-library series
    # entry after every real file under it was archived away) until something prompts a
    # fresh scan. Skipped for dry runs and when nothing was actually archived.
    if not dry_run and succeeded > 0:
        jellyfin = JellyfinClient(
            config.jellyfin_url, config.jellyfin_api_key, config.jellyfin_scan_task_id
        )
        try:
            jellyfin.refresh_all_libraries()
        except JellyfinApiError as exc:
            log.warning("Jellyfin library refresh failed: %s", exc)

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
