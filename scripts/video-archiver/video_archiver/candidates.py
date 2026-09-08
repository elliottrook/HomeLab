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
    # The movie's own id (Radarr) / the parent episode's own id, distinct from the file id
    # (Sonarr) — needed to unmonitor after delete, so Radarr/Sonarr don't see a
    # "monitored but missing" entry and re-search/re-download the archived content.
    # Confirmed by live testing (2026-09-07): DELETE .../episodefile/{id} does NOT
    # unmonitor the episode on its own.
    arr_parent_id: int


def _parse_arr_datetime(value: str) -> datetime:
    # Radarr/Sonarr return ISO-8601 UTC timestamps, e.g. "2026-02-01T03:14:00Z".
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _to_host_path(arr_path: Path, container_root: Path, host_root: Path) -> Path | None:
    """Translate a path as reported by the Radarr/Sonarr API (relative to that app's
    own container mount) into the real host filesystem path this tool reads/writes.
    Returns None if arr_path isn't under container_root — caller skips rather than guesses."""
    try:
        rel = arr_path.relative_to(container_root)
    except ValueError:
        return None
    return host_root / rel


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

        source_path = _to_host_path(
            Path(movie_file["path"]), config.radarr_container_root, config.host_data_root
        )
        movie_folder = _to_host_path(
            Path(movie["path"]), config.radarr_container_root, config.host_data_root
        )
        if source_path is None or movie_folder is None:
            continue

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
                arr_parent_id=movie["id"],
            )
        )

    return out


def find_episode_candidates(sonarr: SonarrClient, config: Config) -> list[Candidate]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.age_threshold_days)
    out: list[Candidate] = []

    for series in sonarr.get_series():
        series_folder = _to_host_path(
            Path(series["path"]), config.sonarr_container_root, config.host_data_root
        )
        if series_folder is None:
            continue
        try:
            rel_folder = series_folder.relative_to(config.tv_current_root)
        except ValueError:
            continue

        # The episodefile resource has no back-reference to its parent episode — the
        # episode resource points the other way instead, via episodeFileId. Build that
        # lookup once per series so each file can be unmonitored (not just deleted) later.
        episode_id_by_file_id = {
            ep["episodeFileId"]: ep["id"]
            for ep in sonarr.get_episodes(series["id"])
            if ep.get("episodeFileId")
        }

        # Anchor eligibility on the EARLIEST dateAdded within each season (when its first
        # episode was downloaded), not each file's own dateAdded. A season that trickles
        # in episode-by-episode over many weeks (e.g. a weekly-release show) would
        # otherwise archive piecemeal, with the season's last episode holding up nothing
        # but itself while earlier episodes leave one at a time — and worse, a season
        # airing over N weeks would take that same N weeks just to finish moving, on top
        # of the age threshold. Anchoring on the season's start makes the whole season
        # age out and move together in one pass, the way a viewer actually thinks of it.
        files_by_season: dict[int, list[dict]] = {}
        for ep_file in sonarr.get_episode_files(series["id"]):
            files_by_season.setdefault(ep_file.get("seasonNumber", 0), []).append(ep_file)

        for season_number, season_files in files_by_season.items():
            season_start = min(_parse_arr_datetime(f["dateAdded"]) for f in season_files)
            if season_start >= cutoff:
                continue  # whole season not old enough yet

            for ep_file in season_files:
                parent_episode_id = episode_id_by_file_id.get(ep_file["id"])
                if parent_episode_id is None:
                    # No monitored-episode record maps to this file — skip rather than
                    # delete a file we couldn't also unmonitor.
                    continue

                source_path = _to_host_path(
                    Path(ep_file["path"]), config.sonarr_container_root, config.host_data_root
                )
                if source_path is None:
                    continue
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
                        date_added=_parse_arr_datetime(ep_file["dateAdded"]),
                        archive_dest_path=archive_dest,
                        delete_fn_name="delete_episode_file",
                        arr_parent_id=parent_episode_id,
                    )
                )

    return out
