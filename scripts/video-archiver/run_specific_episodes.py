#!/usr/bin/env python3
"""One-off, manually targeted run for the Video Library Archiving project's Milestone 2
supervised live test: processes an explicit list of Sonarr episode file IDs through the real
transcode/verify/move/Sonarr-delete-file pipeline, completely bypassing the age-threshold
candidate discovery in candidates.py. Not part of the scheduled/unattended tool — for this one
manual, human-directed test only."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from video_archiver.arr_client import RadarrClient, SonarrClient
from video_archiver.candidates import Candidate, _parse_arr_datetime, _to_host_path
from video_archiver.config import Config
from video_archiver.jellyfin_client import JellyfinApiError, JellyfinClient
from video_archiver.pipeline import RunLogger, _process_one

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

SERIES_ID = 8  # Furious
EPISODE_FILE_IDS = [108, 109, 110, 111, 443, 479, 510, 694]  # S01E01-E08, oldest first

# Optional narrowing for validation runs, e.g. ONLY_FILE_IDS="108" to test just one episode
# before trusting the rest to an unattended batch. Unset/empty runs the full list above.
_only = os.environ.get("ONLY_FILE_IDS", "").strip()
if _only:
    EPISODE_FILE_IDS = [int(x) for x in _only.split(",") if x.strip()]


def main() -> int:
    config = Config.load(Path("config.json"))
    sonarr = SonarrClient(config.sonarr_url, config.sonarr_api_key)
    radarr = RadarrClient(config.radarr_url, config.radarr_api_key)
    run_log = RunLogger(config.log_dir)

    series = next(s for s in sonarr.get_series() if s["id"] == SERIES_ID)
    series_folder = _to_host_path(
        Path(series["path"]), config.sonarr_container_root, config.host_data_root
    )
    rel_folder = series_folder.relative_to(config.tv_current_root)

    all_files = {f["id"]: f for f in sonarr.get_episode_files(SERIES_ID)}
    episode_id_by_file_id = {
        ep["episodeFileId"]: ep["id"]
        for ep in sonarr.get_episodes(SERIES_ID)
        if ep.get("episodeFileId")
    }

    candidates: list[Candidate] = []
    for fid in EPISODE_FILE_IDS:
        ep_file = all_files[fid]
        source_path = _to_host_path(
            Path(ep_file["path"]), config.sonarr_container_root, config.host_data_root
        )
        season_number = ep_file.get("seasonNumber", 0)
        archive_dest = (
            config.tv_archive_root
            / rel_folder
            / f"Season {season_number:02d}"
            / source_path.with_suffix(".mkv").name
        )
        candidates.append(
            Candidate(
                kind="episode",
                arr_file_id=fid,
                title=f"{series['title']} - {source_path.name}",
                source_path=source_path,
                size_bytes=int(ep_file.get("size", 0)),
                date_added=_parse_arr_datetime(ep_file["dateAdded"]),
                archive_dest_path=archive_dest,
                delete_fn_name="delete_episode_file",
                arr_parent_id=episode_id_by_file_id[fid],
            )
        )

    succeeded = failed = 0
    for c in candidates:
        print(f"=== Processing {c.title} ({c.size_bytes/1e9:.2f} GB) ===", flush=True)
        ok = _process_one(c, config, dry_run=False, radarr=radarr, sonarr=sonarr, run_log=run_log)
        print(f"  -> {'OK' if ok else 'FAILED'}", flush=True)
        succeeded += int(ok)
        failed += int(not ok)

    if succeeded > 0:
        jellyfin = JellyfinClient(
            config.jellyfin_url, config.jellyfin_api_key, config.jellyfin_scan_task_id
        )
        try:
            jellyfin.refresh_all_libraries()
            print("Jellyfin library refresh triggered.")
        except JellyfinApiError as exc:
            print(f"Jellyfin library refresh failed: {exc}")

    print(f"\nDone: {succeeded} succeeded, {failed} failed. Log: {run_log.path}")
    run_log.close()
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
