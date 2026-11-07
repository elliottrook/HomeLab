"""Read-only M4 gate observation for one snapshot-free certified movie.

Emits booleans and counts only. This is diagnostic, never deletion authority.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from .lifecycle_policy import calendar_months_before
from .retention_activity_live import collect_active_item_ids
from .retention_audit import _container_db, _pool_usage
from .retention_playback import read_playback_log_evidence
from .retention_queue_live import collect_queue
from .retention_reclaim import estimate_unprotected_file, snapshot_names
from .retention_seasons_live import _mapped_path, collect_season_paths
from .retention_scope_activity import scope_has_active_work
from .retention_subtitles_live import inspect_subtitles, jellyfin_container_probe
from .retention_watch_live import collect_user_views, scope_watch_evidence
from .retention_years_live import LiveYearConfig, _host_path, collect_movie_years


def _fetch_queue(url: str, headers: dict[str, str]) -> tuple[int, object]:
    try:
        with build_opener(ProxyHandler({})).open(
            Request(url, headers=headers), timeout=30,
        ) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, None


def observe(config_path: Path, data_root: Path, *, archive: bool = False) -> dict:
    config = json.loads(config_path.read_text())
    if not isinstance(config, dict):
        raise RuntimeError("archiver configuration malformed")
    jellyfin_key = os.environ.get("JELLYFIN_API_KEY", "")
    radarr_key = os.environ.get("RADARR_API_KEY", "")
    if not jellyfin_key or not radarr_key:
        raise RuntimeError("existing service credential unavailable")
    radarr = _container_db("radarr", "radarr.db")
    jellyfin = _container_db("jellyfin", "data/data/jellyfin.db")
    jellyfin_url = str(config["jellyfin_url"])
    years = collect_movie_years(LiveYearConfig(
        radarr, jellyfin, data_root, jellyfin_url, jellyfin_key,
    ), today=date.today())
    snapshots = snapshot_names()
    snapshot_free = []
    for film in years.certified_facts:
        host = _host_path(film.path, data_root)
        if host and estimate_unprotected_file(
            host, data_root=data_root, snapshots=snapshots,
        ).bytes > 0:
            snapshot_free.append((film, host))
    if archive:
        archive_facts = sorted(
            (row for row in years.certified_facts
             if row.path.startswith("/media/archive-movies/")),
            key=lambda row: row.provider_id or "",
        )
        if not archive_facts:
            return {"status": "held_no_certified_archive_movie", "deletion_enabled": False}
        film = archive_facts[0]
        host = _host_path(film.path, data_root)
        if host is None:
            raise RuntimeError("certified movie path changed")
    else:
        if len(snapshot_free) != 1:
            return {"status": "held_scope_count", "snapshot_free_certified_movies": len(snapshot_free)}
        film, host = snapshot_free[0]
    with closing(sqlite3.connect(f"{radarr.as_uri()}?mode=ro", uri=True)) as db:
        file_rows = list(db.execute("""
            SELECT f.DateAdded,m.Monitored FROM Movies m
            JOIN MovieFiles f ON f.Id=m.MovieFileId WHERE m.Id=?
        """, (film.arr_movie_id,)))
    with closing(sqlite3.connect(f"{jellyfin.as_uri()}?mode=ro", uri=True)) as db:
        users = frozenset(str(row[0]) for row in db.execute("SELECT Id FROM Users"))
    if len(users) != 7:
        raise RuntimeError("household user roster changed")
    views = collect_user_views((film.jellyfin_item_id,), user_ids=users,
                               jellyfin_url=jellyfin_url, jellyfin_api_key=jellyfin_key)
    watch = scope_watch_evidence((film.jellyfin_item_id,), views, users,
                                 read_playback_log_evidence(jellyfin))
    active = collect_active_item_ids(jellyfin_url, jellyfin_key)
    queue = collect_queue("radarr", str(config["radarr_url"]), radarr_key,
                          fetch=_fetch_queue)
    activity = scope_has_active_work(
        kind="movie", arr_id=film.arr_movie_id,
        jellyfin_item_ids=(film.jellyfin_item_id,),
        active_jellyfin_item_ids=active, queue=queue,
    )
    try:
        inspect_subtitles(host, data_root=data_root,
                          probe=lambda path: jellyfin_container_probe(path, data_root=data_root))
        subtitle_structure = True
    except RuntimeError:
        subtitle_structure = False
    import_age = False
    if len(file_rows) == 1 and isinstance(file_rows[0][0], str):
        imported = datetime.fromisoformat(file_rows[0][0].replace("Z", "+00:00"))
        import_age = bool(imported.tzinfo and imported <= calendar_months_before(
            datetime.now(timezone.utc), 3,
        ))
    _, _, cap = _pool_usage()
    return {
        "status": "observed_only", "snapshot_free": any(
            row.provider_id == film.provider_id for row, _ in snapshot_free),
        "snapshot_free_certified_movies": len(snapshot_free),
        "in_archive": film.path.startswith("/media/archive-movies/"),
        "radarr_file_record_unique": len(file_rows) == 1,
        "radarr_monitored": bool(file_rows[0][1]) if len(file_rows) == 1 else None,
        "three_month_import_age_met": import_age,
        "seven_user_watch_complete": watch is not None,
        "watch_or_playback_protected": (None if watch is None else
                                        bool(watch[1] or any(row.protected for row in watch[0]))),
        "active_playback_or_queue": activity,
        "subtitle_structure_verified": subtitle_structure,
        "pool_trigger_met": cap >= 60,
        "notice_verified": False,
        "deletion_enabled": False,
    }


def observe_season(config_path: Path, data_root: Path) -> dict:
    """Observe one bounded provider-certified Archive season; never act."""
    config = json.loads(config_path.read_text())
    if not isinstance(config, dict):
        raise RuntimeError("archiver configuration malformed")
    jellyfin_key = os.environ.get("JELLYFIN_API_KEY", "")
    sonarr_key = os.environ.get("SONARR_API_KEY", "")
    if not jellyfin_key or not sonarr_key:
        raise RuntimeError("existing service credential unavailable")
    sonarr = _container_db("sonarr", "sonarr.db")
    jellyfin = _container_db("jellyfin", "data/data/jellyfin.db")
    scopes = collect_season_paths(sonarr, jellyfin, data_root)
    with closing(sqlite3.connect(f"{sonarr.as_uri()}?mode=ro", uri=True)) as db:
        series_paths = dict(db.execute("SELECT Id,Path FROM Series"))
        selected = next((scope for scope in sorted(scopes.certified_scope_item_ids)
                         if str(series_paths.get(scope[0], "")).startswith(
                             "/media/tv/archive-tv/")), None)
        if selected is None:
            return {"status": "held_no_certified_archive_season", "deletion_enabled": False}
        series_id, season_number = selected
        file_rows = list(db.execute("""
            SELECT RelativePath,DateAdded FROM EpisodeFiles
            WHERE SeriesId=? AND SeasonNumber=?
        """, selected))
    if not file_rows or len(file_rows) > 30:
        return {"status": "held_season_file_bound", "deletion_enabled": False}
    host_files = []
    for relative, _ in file_rows:
        mapped = _mapped_path(series_paths[series_id], relative)
        host = _host_path(mapped, data_root) if mapped else None
        if host is None or not host.is_file():
            raise RuntimeError("certified season file changed")
        host_files.append(host)
    snapshots = snapshot_names()
    snapshot_free = all(estimate_unprotected_file(
        host, data_root=data_root, snapshots=snapshots,
    ).bytes > 0 for host in host_files)
    with closing(sqlite3.connect(f"{jellyfin.as_uri()}?mode=ro", uri=True)) as db:
        users = frozenset(str(row[0]) for row in db.execute("SELECT Id FROM Users"))
    if len(users) != 7:
        raise RuntimeError("household user roster changed")
    item_ids = scopes.certified_scope_item_ids[selected]
    jellyfin_url = str(config["jellyfin_url"])
    views = collect_user_views(item_ids, user_ids=users,
                               jellyfin_url=jellyfin_url, jellyfin_api_key=jellyfin_key)
    watch = scope_watch_evidence(item_ids, views, users,
                                 read_playback_log_evidence(jellyfin))
    active = collect_active_item_ids(jellyfin_url, jellyfin_key)
    queue = collect_queue("sonarr", str(config["sonarr_url"]), sonarr_key,
                          fetch=_fetch_queue)
    activity = scope_has_active_work(
        kind="season", arr_id=series_id, jellyfin_item_ids=item_ids,
        active_jellyfin_item_ids=active, queue=queue,
    )
    subtitle_structure = True
    for host in host_files:
        try:
            inspect_subtitles(host, data_root=data_root,
                              probe=lambda path: jellyfin_container_probe(
                                  path, data_root=data_root))
        except RuntimeError:
            subtitle_structure = False
            break
    age_ok = True
    for _, added in file_rows:
        if not isinstance(added, str):
            age_ok = False
            break
        imported = datetime.fromisoformat(added.replace("Z", "+00:00"))
        if not imported.tzinfo or imported > calendar_months_before(
            datetime.now(timezone.utc), 3,
        ):
            age_ok = False
            break
    _, _, cap = _pool_usage()
    return {
        "status": "observed_only", "scope_kind": "season",
        "file_count": len(file_rows), "snapshot_free": snapshot_free,
        "three_month_youngest_import_age_met": age_ok,
        "seven_user_watch_complete": watch is not None,
        "watch_or_playback_protected": (None if watch is None else
                                        bool(watch[1] or any(row.protected for row in watch[0]))),
        "active_playback_or_queue": activity,
        "subtitle_structure_verified": subtitle_structure,
        "pool_trigger_met": cap >= 60, "notice_verified": False,
        "deletion_enabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--kind", choices=("movie", "archive-movie", "season"),
                        default="movie")
    args = parser.parse_args()
    try:
        result = (observe_season(args.config, args.data_root) if args.kind == "season"
                  else observe(args.config, args.data_root,
                               archive=args.kind == "archive-movie"))
    except (RuntimeError, ValueError, OSError, sqlite3.Error, KeyError):
        result = {"status": "held_source_uncertain", "deletion_enabled": False}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
