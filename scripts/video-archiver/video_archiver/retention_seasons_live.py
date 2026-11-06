"""Read-only Sonarr/Jellyfin season path audit; no deletion authority."""

from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .retention_years_live import _connect_readonly, _host_path


EPISODE_TYPE = "MediaBrowser.Controller.Entities.TV.Episode"


@dataclass(frozen=True)
class SeasonPathAudit:
    sonarr_file_rows: int
    exact_file_rows: int
    season_scopes: int
    exact_season_scopes: int
    held_reasons: dict[str, int]


def _mapped_path(series_path: object, relative: object) -> str | None:
    if not isinstance(series_path, str) or not isinstance(relative, str):
        return None
    if not series_path.startswith("/media/tv/") or not relative or relative.startswith("/"):
        return None
    if ".." in relative.split("/") or ".." in series_path.split("/"):
        return None
    return "/media/" + (series_path.rstrip("/") + "/" + relative)[len("/media/tv/"):]


def collect_season_paths(sonarr_db: Path, jellyfin_db: Path,
                         data_root: Path) -> SeasonPathAudit:
    """Certify path coverage only; watch, age, subtitles and reclaim are separate."""
    with closing(_connect_readonly(sonarr_db)) as sonarr, closing(_connect_readonly(jellyfin_db)) as jellyfin:
        series_paths = {row[0]: row[1] for row in sonarr.execute("SELECT Id,Path FROM Series")}
        refs: dict[int, set[tuple[int, int]]] = defaultdict(set)
        for file_id, series_id, season in sonarr.execute(
            "SELECT EpisodeFileId,SeriesId,SeasonNumber FROM Episodes WHERE EpisodeFileId>0"
        ):
            refs[file_id].add((series_id, season))
        jellyfin_paths: Counter[str] = Counter()
        jf_seasons: dict[str, set[int | None]] = defaultdict(set)
        for path, season in jellyfin.execute(
            "SELECT Path,ParentIndexNumber FROM BaseItems WHERE Type=? AND Path IS NOT NULL",
            (EPISODE_TYPE,),
        ):
            jellyfin_paths[str(path)] += 1
            jf_seasons[str(path)].add(season if type(season) is int else None)
        scope_paths: dict[tuple[int, int], set[str]] = defaultdict(set)
        scope_holds: dict[tuple[int, int], set[str]] = defaultdict(set)
        exact_files = 0
        file_records = list(sonarr.execute(
            "SELECT Id,SeriesId,SeasonNumber,RelativePath FROM EpisodeFiles"
        ))
        mapped_counts = Counter(
            mapped for _, series_id, _, relative in file_records
            if (mapped := _mapped_path(series_paths.get(series_id), relative)) is not None
        )
        for file_id, series_id, season, relative in file_records:
            if type(season) is not int or season < 0:
                continue
            scope = (series_id, season)
            mapped = _mapped_path(series_paths.get(series_id), relative)
            if mapped is None:
                scope_holds[scope].add("invalid Sonarr path")
                continue
            scope_paths[scope].add(mapped)
            physical = _host_path(mapped, data_root)
            if refs.get(file_id) != {scope}:
                scope_holds[scope].add("episode reference missing or crosses season")
            elif mapped_counts[mapped] != 1:
                scope_holds[scope].add("duplicate Sonarr file path")
            elif jellyfin_paths[mapped] != 1:
                scope_holds[scope].add("Jellyfin path absent or duplicated")
            elif physical is None or not physical.is_file():
                scope_holds[scope].add("physical file absent")
            else:
                exact_files += 1
        # A Jellyfin file under a Sonarr series root with no matching Sonarr
        # file means that season's scope is incomplete. Unknown season holds
        # every scope for that series.
        for series_id, root in series_paths.items():
            root_probe = _mapped_path(root, "__root__")
            if root_probe is None:
                continue
            mapped_root = root_probe.rsplit("/", 1)[0]
            known = {p for (sid, _), paths in scope_paths.items() if sid == series_id for p in paths}
            scopes = {scope for scope in scope_paths | scope_holds if scope[0] == series_id}
            for path, seasons in jf_seasons.items():
                if not path.startswith(mapped_root + "/") or path in known:
                    continue
                if None in seasons:
                    affected = scopes
                else:
                    affected = {(series_id, season) for season in seasons if (series_id, season) in scopes}
                for scope in affected:
                    scope_holds[scope].add("unowned Jellyfin episode in series root")
        all_scopes = set(scope_paths) | set(scope_holds)
        reasons = Counter(reason for scope in all_scopes for reason in scope_holds[scope])
        return SeasonPathAudit(len(file_records), exact_files, len(all_scopes),
                               sum(not scope_holds[scope] for scope in all_scopes), dict(sorted(reasons.items())))
