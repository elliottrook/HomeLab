"""Read-only aggregate M4 audit. No ARR or media mutation capability."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
from collections import Counter
from contextlib import closing
from datetime import date
from pathlib import Path

from .retention_reclaim import estimate_unprotected_file, snapshot_names
from .retention_activity_live import collect_active_item_ids
from .retention_seasons_live import collect_season_paths
from .retention_playback import read_playback_log_evidence
from .retention_watch_live import collect_user_views, scope_watch_evidence
from .retention_years_live import LiveYearConfig, _host_path, collect_movie_years


def _pool_usage() -> tuple[int, int, int]:
    result = subprocess.run(
        ["zpool", "list", "-H", "-p", "-o", "size,alloc,cap", "Media"],
        capture_output=True, text=True, timeout=30, check=True,
    )
    fields = result.stdout.strip().split()
    if len(fields) != 3:
        raise RuntimeError("unexpected pool accounting")
    size, allocated = (int(fields[0]), int(fields[1]))
    cap = int(fields[2].rstrip("%"))
    if size <= 0 or allocated < 0 or allocated > size or not 0 <= cap <= 100:
        raise RuntimeError("invalid pool accounting")
    return size, allocated, cap


def _container_db(container: str, relative: str) -> Path:
    if container not in ("radarr", "sonarr", "jellyfin"):
        raise ValueError("unexpected container")
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{json .Mounts}}", container],
        capture_output=True, text=True, timeout=30, check=True,
    )
    mounts = json.loads(result.stdout)
    roots = [Path(row["Source"]) for row in mounts if row.get("Destination") == "/config"]
    if len(roots) != 1:
        raise RuntimeError("expected one private app config mount")
    path = roots[0] / relative
    if not path.is_file():
        raise RuntimeError("app database unavailable")
    return path


def audit(radarr_db: Path, sonarr_db: Path, jellyfin_db: Path, data_root: Path,
          jellyfin_url: str, jellyfin_key: str) -> dict:
    size, allocated, cap = _pool_usage()
    years = collect_movie_years(LiveYearConfig(
        radarr_db, jellyfin_db, data_root, jellyfin_url, jellyfin_key,
    ), today=date.today())
    playback = read_playback_log_evidence(jellyfin_db)
    active_items = collect_active_item_ids(jellyfin_url, jellyfin_key)
    seasons = collect_season_paths(sonarr_db, jellyfin_db, data_root)
    sample_scopes = sorted(seasons.certified_scope_item_ids)[:2]
    watch_sample: Counter[str] = Counter()
    movie_sample = sorted(years.certified_facts, key=lambda row: row.provider_id or "")[:2]
    movie_watch_sample: Counter[str] = Counter()
    if sample_scopes or movie_sample:
        with closing(sqlite3.connect(f"{jellyfin_db.as_uri()}?mode=ro", uri=True)) as db:
            user_ids = frozenset(str(row[0]) for row in db.execute("SELECT Id FROM Users"))
        if len(user_ids) != 7:
            raise RuntimeError("household user roster changed")
        item_ids = tuple(sorted(
            {item for scope in sample_scopes
             for item in seasons.certified_scope_item_ids[scope]}
            | {row.jellyfin_item_id for row in movie_sample}
        ))
        views = collect_user_views(item_ids, user_ids=user_ids,
                                   jellyfin_url=jellyfin_url, jellyfin_api_key=jellyfin_key)
        for scope in sample_scopes:
            observation = scope_watch_evidence(
                seasons.certified_scope_item_ids[scope], views, user_ids, playback)
            if observation is None:
                watch_sample["held_incomplete"] += 1
            elif observation[1] or any(row.protected for row in observation[0]):
                watch_sample["protected"] += 1
            else:
                watch_sample["observed_unwatched"] += 1
        for movie in movie_sample:
            observation = scope_watch_evidence(
                (movie.jellyfin_item_id,), views, user_ids, playback)
            if observation is None:
                movie_watch_sample["held_incomplete"] += 1
            elif observation[1] or any(row.protected for row in observation[0]):
                movie_watch_sample["protected"] += 1
            else:
                movie_watch_sample["observed_unwatched"] += 1
    snapshots = tuple(reversed(snapshot_names()))
    coverage: Counter[str] = Counter()
    with closing(sqlite3.connect(f"{jellyfin_db.as_uri()}?mode=ro", uri=True)) as db:
        for path, kind in db.execute(
            "SELECT Path,Type FROM BaseItems WHERE Type IN (?,?) AND Path LIKE '/media/%'",
            ("MediaBrowser.Controller.Entities.Movies.Movie",
             "MediaBrowser.Controller.Entities.TV.Episode"),
        ):
            host_path = _host_path(str(path), data_root)
            if host_path is None or not host_path.is_file():
                coverage["missing_or_invalid"] += 1
                continue
            item = "movie" if kind.endswith(".Movie") else "episode"
            coverage[item + "_present"] += 1
            estimate = estimate_unprotected_file(host_path, data_root=data_root,
                                                 snapshots=snapshots)
            if estimate.reason == "file retained by snapshot":
                coverage[item + "_snapshot_covered"] += 1
            elif estimate.bytes > 0:
                coverage[item + "_potentially_reclaimable"] += 1
            else:
                coverage[item + "_held_other"] += 1
    return {
        "pool_size_bytes": size,
        "pool_allocated_bytes": allocated,
        "pool_cap_percent": cap,
        "triggered": 100 * allocated >= 60 * size,
        "urgent_alert": 100 * allocated >= 62 * size,
        "movie_year_inventory": {
            "examined": years.examined, "certified": years.counted,
            "held": years.held, "years": len(years.counts),
            "singleton_years": sum(count == 1 for count in years.counts.values()),
        },
        "retained_playback": {
            "event_count": playback.event_count,
            "distinct_item_count": len(playback.item_ids),
            "first_event": playback.first_event,
            "last_event": playback.last_event,
        },
        "active_playback_item_count": len(active_items),
        "season_path_inventory": {
            "sonarr_file_rows": seasons.sonarr_file_rows,
            "exact_file_rows": seasons.exact_file_rows,
            "season_scopes": seasons.season_scopes,
            "exact_season_scopes": seasons.exact_season_scopes,
            "held_reasons": seasons.held_reasons,
            "provider_certified_season_scopes": seasons.provider_certified_season_scopes,
            "identity_held_reasons": seasons.identity_held_reasons,
        },
        "season_watch_sample": {
            "sampled": len(sample_scopes),
            "held_incomplete": watch_sample["held_incomplete"],
            "protected": watch_sample["protected"],
            "observed_unwatched": watch_sample["observed_unwatched"],
        },
        "movie_watch_sample": {
            "sampled": len(movie_sample),
            "held_incomplete": movie_watch_sample["held_incomplete"],
            "protected": movie_watch_sample["protected"],
            "observed_unwatched": movie_watch_sample["observed_unwatched"],
        },
        "media_data_snapshot_count": len(snapshots),
        "physical_inventory": dict(sorted(coverage.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radarr-db", type=Path)
    parser.add_argument("--sonarr-db", type=Path)
    parser.add_argument("--jellyfin-db", type=Path)
    parser.add_argument("--discover-docker", action="store_true")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--jellyfin-url", required=True)
    args = parser.parse_args()
    key = os.environ.get("JELLYFIN_API_KEY")
    if not key:
        raise SystemExit("JELLYFIN_API_KEY is required")
    if args.discover_docker:
        if args.radarr_db or args.sonarr_db or args.jellyfin_db:
            raise SystemExit("use explicit DB paths or --discover-docker, not both")
        radarr_db = _container_db("radarr", "radarr.db")
        sonarr_db = _container_db("sonarr", "sonarr.db")
        jellyfin_db = _container_db("jellyfin", "data/data/jellyfin.db")
    elif args.radarr_db and args.sonarr_db and args.jellyfin_db:
        radarr_db, sonarr_db, jellyfin_db = args.radarr_db, args.sonarr_db, args.jellyfin_db
    else:
        raise SystemExit("all three DB paths or --discover-docker are required")
    print(json.dumps(audit(radarr_db, sonarr_db, jellyfin_db,
                           args.data_root, args.jellyfin_url, key), sort_keys=True))


if __name__ == "__main__":
    main()
