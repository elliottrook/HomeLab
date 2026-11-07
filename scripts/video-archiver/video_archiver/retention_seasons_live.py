"""Read-only Sonarr/Jellyfin season path audit; no deletion authority."""

from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .retention_years_live import _connect_readonly, _host_path, _item_id


EPISODE_TYPE = "MediaBrowser.Controller.Entities.TV.Episode"
SERIES_TYPE = "MediaBrowser.Controller.Entities.TV.Series"
SEASON_TYPE = "MediaBrowser.Controller.Entities.TV.Season"


@dataclass(frozen=True)
class SeasonPathAudit:
    sonarr_file_rows: int
    exact_file_rows: int
    season_scopes: int
    exact_season_scopes: int
    held_reasons: dict[str, int]
    provider_certified_season_scopes: int
    identity_held_reasons: dict[str, int]


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
        sonarr_version = sonarr.execute("PRAGMA data_version").fetchone()[0]
        jellyfin_version = jellyfin.execute("PRAGMA data_version").fetchone()[0]
        series_rows = list(sonarr.execute("SELECT Id,Path,TvdbId FROM Series"))
        series_paths = {series_id: path for series_id, path, _ in series_rows}
        sonarr_tvdb_counts = Counter(str(tvdb) for _, _, tvdb in series_rows if tvdb)
        jf_providers: dict[str, list[str]] = defaultdict(list)
        for item_id, value in jellyfin.execute(
            "SELECT ItemId,ProviderValue FROM BaseItemProviders WHERE ProviderId='Tvdb'"
        ):
            jf_providers[_item_id(item_id)].append(str(value))
        jf_series_by_tvdb: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for item_id, path in jellyfin.execute(
            "SELECT Id,Path FROM BaseItems WHERE Type=?", (SERIES_TYPE,),
        ):
            normalized = _item_id(item_id)
            providers = jf_providers[normalized]
            if len(providers) == 1 and path:
                jf_series_by_tvdb[providers[0]].append((normalized, str(path)))
        matched_series: dict[int, str] = {}
        for series_id, path, tvdb in series_rows:
            mapped_probe = _mapped_path(path, "__root__")
            matches = jf_series_by_tvdb.get(str(tvdb), ())
            if (tvdb and sonarr_tvdb_counts[str(tvdb)] == 1
                    and mapped_probe is not None and len(matches) == 1
                    and matches[0][1] == mapped_probe.rsplit("/", 1)[0]):
                matched_series[series_id] = matches[0][0]
        jf_season_rows: dict[str, list[tuple[str, int | None]]] = defaultdict(list)
        for season_id, series_id, season_number in jellyfin.execute(
            "SELECT Id,SeriesId,IndexNumber FROM BaseItems WHERE Type=?", (SEASON_TYPE,),
        ):
            jf_season_rows[_item_id(season_id)].append((
                _item_id(series_id) if series_id else "",
                season_number if type(season_number) is int else None,
            ))
        refs: dict[int, set[tuple[int, int]]] = defaultdict(set)
        for file_id, series_id, season in sonarr.execute(
            "SELECT EpisodeFileId,SeriesId,SeasonNumber FROM Episodes WHERE EpisodeFileId>0"
        ):
            refs[file_id].add((series_id, season))
        jellyfin_paths: Counter[str] = Counter()
        jf_seasons: dict[str, set[int | None]] = defaultdict(set)
        jf_episode_facts: dict[str, tuple[int | None, str, str]] = {}
        for path, season, series_id, season_id in jellyfin.execute(
            "SELECT Path,ParentIndexNumber,SeriesId,SeasonId FROM BaseItems WHERE Type=? AND Path IS NOT NULL",
            (EPISODE_TYPE,),
        ):
            jellyfin_paths[str(path)] += 1
            jf_seasons[str(path)].add(season if type(season) is int else None)
            jf_episode_facts[str(path)] = (
                season if type(season) is int else None,
                _item_id(series_id) if series_id else "",
                _item_id(season_id) if season_id else "",
            )
        scope_paths: dict[tuple[int, int], set[str]] = defaultdict(set)
        scope_holds: dict[tuple[int, int], set[str]] = defaultdict(set)
        scope_identity_holds: dict[tuple[int, int], set[str]] = defaultdict(set)
        scope_season_ids: dict[tuple[int, int], set[str]] = defaultdict(set)
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
                jf_season, jf_series_id, jf_season_id = jf_episode_facts[mapped]
                if series_id not in matched_series:
                    scope_identity_holds[scope].add("series provider or root mismatch")
                elif (jf_series_id != matched_series[series_id] or jf_season != season
                      or len(jf_season_rows[jf_season_id]) != 1
                      or jf_season_rows[jf_season_id][0] != (jf_series_id, season)):
                    scope_identity_holds[scope].add("episode season or series ancestor mismatch")
                else:
                    scope_season_ids[scope].add(jf_season_id)
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
        sonarr_by_jf_series = {jf_id: sonarr_id for sonarr_id, jf_id in matched_series.items()}
        for path, (season_number, jf_series_id, _) in jf_episode_facts.items():
            sonarr_id = sonarr_by_jf_series.get(jf_series_id)
            if sonarr_id is None:
                continue
            if season_number is None:
                affected = {scope for scope in all_scopes if scope[0] == sonarr_id}
            else:
                affected = {(sonarr_id, season_number)} & all_scopes
            for scope in affected:
                if path not in scope_paths[scope]:
                    scope_identity_holds[scope].add("unowned Jellyfin episode in provider season")
        for scope in all_scopes:
            if not scope_holds[scope] and len(scope_season_ids[scope]) != 1:
                scope_identity_holds[scope].add("season ancestor missing or inconsistent")
        reasons = Counter(reason for scope in all_scopes for reason in scope_holds[scope])
        identity_reasons = Counter(reason for scope in all_scopes for reason in scope_identity_holds[scope])
        if (sonarr.execute("PRAGMA data_version").fetchone()[0] != sonarr_version
                or jellyfin.execute("PRAGMA data_version").fetchone()[0] != jellyfin_version):
            raise RuntimeError("Sonarr or Jellyfin changed during season inventory")
        return SeasonPathAudit(len(file_records), exact_files, len(all_scopes),
                               sum(not scope_holds[scope] for scope in all_scopes),
                               dict(sorted(reasons.items())),
                               sum(not scope_holds[scope] and not scope_identity_holds[scope]
                                   for scope in all_scopes),
                               dict(sorted(identity_reasons.items())))
