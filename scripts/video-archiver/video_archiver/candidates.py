from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .arr_client import RadarrClient, SonarrClient
from .config import Config


@dataclass
class Candidate:
    kind: str  # "movie" or "episode"
    arr_file_id: int
    title: str
    source_path: Path
    size_bytes: int
    date_added: datetime
    archive_dest_path: Path
    # For logging/API calls after a successful archive.
    delete_fn_name: str  # "delete_movie_file" or "delete_episode_file"


def _parse_arr_datetime(value: str) -> datetime:
    # Radarr/Sonarr return ISO-8601 UTC timestamps, e.g. "2026-02-01T03:14:00Z".
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def find_movie_candidates(radarr: RadarrClient, config: Config) -> list[Candidate]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.age_threshold_days)
    out: list[Candidate] = []

    for movie in radarr.get_movies():
        if not movie.get("hasFile"):
            continue
        movie_file = movie.get("movieFile")
        if not movie_file:
            continue

        date_added = _parse_arr_datetime(movie_file["dateAdded"])
        if date_added >= cutoff:
            continue

        source_path = Path(movie_file["path"])
        movie_folder = Path(movie["path"])
        try:
            rel_folder = movie_folder.relative_to(config.movies_current_root)
        except ValueError:
            # Not under the configured current root — skip rather than guess.
            continue

        archive_dest = config.movies_archive_root / rel_folder / source_path.with_suffix(".mkv").name

        out.append(
            Candidate(
                kind="movie",
                arr_file_id=movie_file["id"],
                title=movie.get("title", str(movie_folder)),
                source_path=source_path,
                size_bytes=int(movie_file.get("size", 0)),
                date_added=date_added,
                archive_dest_path=archive_dest,
                delete_fn_name="delete_movie_file",
            )
        )

    return out


def find_episode_candidates(sonarr: SonarrClient, config: Config) -> list[Candidate]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.age_threshold_days)
    out: list[Candidate] = []

    for series in sonarr.get_series():
        series_folder = Path(series["path"])
        try:
            rel_folder = series_folder.relative_to(config.tv_current_root)
        except ValueError:
            continue

        for ep_file in sonarr.get_episode_files(series["id"]):
            date_added = _parse_arr_datetime(ep_file["dateAdded"])
            if date_added >= cutoff:
                continue

            source_path = Path(ep_file["path"])
            season_number = ep_file.get("seasonNumber", 0)
            archive_dest = (
                config.tv_archive_root
                / rel_folder
                / f"Season {season_number:02d}"
                / source_path.with_suffix(".mkv").name
            )

            out.append(
                Candidate(
                    kind="episode",
                    arr_file_id=ep_file["id"],
                    title=f"{series.get('title', str(series_folder))} - {source_path.name}",
                    source_path=source_path,
                    size_bytes=int(ep_file.get("size", 0)),
                    date_added=date_added,
                    archive_dest_path=archive_dest,
                    delete_fn_name="delete_episode_file",
                )
            )

    return out
