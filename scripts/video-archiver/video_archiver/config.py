from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    radarr_url: str
    sonarr_url: str
    jellyfin_url: str
    jellyfin_scan_task_id: str
    radarr_api_key: str
    sonarr_api_key: str
    jellyfin_api_key: str

    age_threshold_days: int
    target_size_bytes: int
    target_size_min_bytes: int
    target_size_max_bytes: int

    movies_current_root: Path
    tv_current_root: Path
    movies_archive_root: Path
    tv_archive_root: Path

    # Radarr/Sonarr's REST APIs report paths as seen from inside each app's own
    # container (its own bind-mount point), not the host filesystem path this tool
    # (running directly on the host) needs to actually read/probe/transcode a file.
    # Both containers mount the same host_data_root at a different container path.
    host_data_root: Path
    radarr_container_root: Path
    sonarr_container_root: Path

    ffmpeg_bin: str
    ffprobe_bin: str
    vaapi_device: str
    work_dir: Path
    log_dir: Path
    lock_file: Path

    max_files_per_run: int
    nice_level: int
    duration_tolerance_fraction: float

    @staticmethod
    def load(config_path: Path) -> "Config":
        with open(config_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        radarr_api_key = os.environ.get("RADARR_API_KEY", "")
        sonarr_api_key = os.environ.get("SONARR_API_KEY", "")
        jellyfin_api_key = os.environ.get("JELLYFIN_API_KEY", "")
        if not radarr_api_key or not sonarr_api_key or not jellyfin_api_key:
            raise RuntimeError(
                "RADARR_API_KEY, SONARR_API_KEY and JELLYFIN_API_KEY must be set in the "
                "environment; they are deliberately never read from the config file."
            )

        return Config(
            radarr_url=raw["radarr_url"].rstrip("/"),
            sonarr_url=raw["sonarr_url"].rstrip("/"),
            jellyfin_url=raw["jellyfin_url"].rstrip("/"),
            jellyfin_scan_task_id=raw["jellyfin_scan_task_id"],
            radarr_api_key=radarr_api_key,
            sonarr_api_key=sonarr_api_key,
            jellyfin_api_key=jellyfin_api_key,
            age_threshold_days=int(raw["age_threshold_days"]),
            target_size_bytes=int(raw["target_size_bytes"]),
            target_size_min_bytes=int(raw["target_size_min_bytes"]),
            target_size_max_bytes=int(raw["target_size_max_bytes"]),
            movies_current_root=Path(raw["movies_current_root"]),
            tv_current_root=Path(raw["tv_current_root"]),
            movies_archive_root=Path(raw["movies_archive_root"]),
            tv_archive_root=Path(raw["tv_archive_root"]),
            host_data_root=Path(raw["host_data_root"]),
            radarr_container_root=Path(raw["radarr_container_root"]),
            sonarr_container_root=Path(raw["sonarr_container_root"]),
            ffmpeg_bin=raw["ffmpeg_bin"],
            ffprobe_bin=raw["ffprobe_bin"],
            vaapi_device=raw["vaapi_device"],
            work_dir=Path(raw["work_dir"]),
            log_dir=Path(raw["log_dir"]),
            lock_file=Path(raw["lock_file"]),
            max_files_per_run=int(raw["max_files_per_run"]),
            nice_level=int(raw["nice_level"]),
            duration_tolerance_fraction=float(raw["duration_tolerance_fraction"]),
        )
