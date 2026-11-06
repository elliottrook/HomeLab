"""Read-only Jellyfin/Radarr movie-year inventory for the retention controller.

No title, path, user ID or token is logged. A failed API page or incomplete user
roster raises an error, so the controller cannot receive a partial safe count.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener
from urllib.error import HTTPError

from .retention_years import MovieYearFact, MovieYearInventory, count_verified_movie_years


MOVIE_TYPE = "MediaBrowser.Controller.Entities.Movies.Movie"


@dataclass(frozen=True)
class LiveYearConfig:
    radarr_db: Path
    jellyfin_db: Path
    host_data_root: Path
    jellyfin_url: str
    jellyfin_api_key: str
    expected_user_count: int = 7


def _connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise RuntimeError("inventory database unavailable")
    return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)


def _item_id(value: object) -> str:
    return str(value).replace("-", "").lower()


def _host_path(jellyfin_path: str, root: Path) -> Path | None:
    prefix = PurePosixPath("/media")
    path = PurePosixPath(jellyfin_path)
    if ".." in path.parts:
        return None
    try:
        suffix = path.relative_to(prefix)
    except ValueError:
        return None
    candidate = root / suffix
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if not resolved_candidate.is_relative_to(resolved_root):
        return None
    return candidate


def _fetch_json(url: str, headers: dict[str, str]) -> tuple[int, dict]:
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(Request(url, headers=headers), timeout=30) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, {}


FetchJson = Callable[[str, dict[str, str]], tuple[int, dict]]


def _visible_movies(fetch: FetchJson, config: LiveYearConfig, user_id: str) -> set[str]:
    seen: set[str] = set()
    start = 0
    total: int | None = None
    while total is None or start < total:
        query = urlencode({
            "Recursive": "true", "IncludeItemTypes": "Movie",
            "StartIndex": start, "Limit": 500,
        })
        status, payload = fetch(
            f"{config.jellyfin_url.rstrip('/')}/Users/{user_id}/Items?{query}",
            {"Authorization": (
                'MediaBrowser Client="retention-year-audit", Device="TrueNAS", '
                'DeviceId="aster-retention-year-audit", Version="1", '
                f'Token="{config.jellyfin_api_key}"'
            )},
        )
        if status != 200:
            raise RuntimeError(f"Jellyfin household movie page failed: HTTP {status}")
        batch = payload.get("Items")
        count = payload.get("TotalRecordCount")
        if not isinstance(batch, list) or type(count) is not int or count < 0:
            raise RuntimeError("Jellyfin household movie page malformed")
        if total is None:
            total = count
        elif count != total:
            raise RuntimeError("Jellyfin movie count changed during inventory")
        ids = [_item_id(row.get("Id")) for row in batch if isinstance(row, dict)]
        if len(ids) != len(batch) or any(not value or value == "none" for value in ids):
            raise RuntimeError("Jellyfin household movie item missing ID")
        seen.update(ids)
        start += len(batch)
        if not batch and start < total:
            raise RuntimeError("Jellyfin household movie page incomplete")
    if start != total or len(seen) != total:
        raise RuntimeError("Jellyfin household movie pages overlap or are incomplete")
    return seen


def collect_movie_years(config: LiveYearConfig, *, today: date,
                        fetch: FetchJson = _fetch_json) -> MovieYearInventory:
    """Certify conservative lower-bound counts from a complete source scan."""
    if not config.jellyfin_api_key or config.expected_user_count <= 0:
        raise ValueError("Jellyfin key and expected household size are required")
    with closing(_connect_readonly(config.jellyfin_db)) as jellyfin, closing(_connect_readonly(config.radarr_db)) as radarr:
            user_ids = [str(row[0]) for row in jellyfin.execute("SELECT Id FROM Users")]
            if len(user_ids) != config.expected_user_count or len(set(user_ids)) != len(user_ids):
                raise RuntimeError("household user roster changed")
            views = {user: _visible_movies(fetch, config, user) for user in user_ids}
            provider_rows: dict[str, list[str]] = defaultdict(list)
            for item_id, provider_value in jellyfin.execute(
                "SELECT ItemId,ProviderValue FROM BaseItemProviders WHERE ProviderId='Tmdb'"
            ):
                provider_rows[_item_id(item_id)].append(str(provider_value))
            arr_rows: dict[str, list[tuple[int, str | None, bool]]] = defaultdict(list)
            for movie_id, tmdb, year, folder, selected_file_id, file_id, relative in radarr.execute("""
                SELECT m.Id, md.TmdbId, md.Year, m.Path, m.MovieFileId, f.Id, f.RelativePath
                FROM Movies m JOIN MovieMetadata md ON md.Id=m.MovieMetadataId
                LEFT JOIN MovieFiles f ON f.MovieId=m.Id
            """):
                if tmdb is None:
                    continue
                mapped = None
                if file_id is not None and folder and relative and folder.startswith("/media/movie/"):
                    mapped = "/media/" + (folder.rstrip("/") + "/" + relative)[len("/media/movie/"):]
                arr_rows[str(tmdb)].append((year, mapped, file_id is not None and selected_file_id == file_id))
            facts: list[MovieYearFact] = []
            for item_id, path, year in jellyfin.execute(
                "SELECT Id,Path,ProductionYear FROM BaseItems WHERE Type=? AND Path IS NOT NULL",
                (MOVIE_TYPE,),
            ):
                item = _item_id(item_id)
                path = str(path)
                providers = provider_rows[item]
                provider = providers[0] if len(providers) == 1 else None
                matches = arr_rows.get(provider or "", ())
                mapped = _host_path(path, config.host_data_root)
                facts.append(MovieYearFact(
                    provider_id=f"tmdb:{provider}" if provider else None,
                    release_year=year,
                    jellyfin_item_id=item,
                    path=path,
                    physical_present=bool(mapped and mapped.is_file()),
                    arr_identity_verified=(len(matches) == 1 and matches[0] == (year, path, True)),
                    visible_user_ids=frozenset(user for user, visible in views.items() if item in visible),
                ))
            return count_verified_movie_years(
                tuple(facts), expected_user_ids=frozenset(user_ids),
                source_scan_complete=True, today=today,
            )
