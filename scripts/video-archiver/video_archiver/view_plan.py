"""Build a preview-only Kodi TV view plan from reconciled ARR/Kodi facts.

The caller must verify legacy Archive membership against a pre-migration
checkpoint and persist first-seen dates outside Git. Incomplete plans must not
be published as a replacement for the household's full TV view.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from .lifecycle_policy import FileAgeSize, age_size_eligibility
from .view_nodes import SeasonView, SeriesView


@dataclass(frozen=True)
class ArrSeason:
    number: int
    files: tuple[FileAgeSize, ...]


@dataclass(frozen=True)
class ArrSeries:
    arr_id: int
    tvdb_id: int | None
    seasons: tuple[ArrSeason, ...]


@dataclass(frozen=True)
class KodiSeries:
    kodi_id: int
    tvdb_id: int | None
    display_title: str


@dataclass(frozen=True)
class HeldSeries:
    arr_id: int
    reason: str


@dataclass(frozen=True)
class TvViewPlan:
    series: tuple[SeriesView, ...]
    held: tuple[HeldSeries, ...]
    skipped_empty: tuple[int, ...]

    def require_complete(self) -> tuple[SeriesView, ...]:
        """Return publishable series only when every ARR series is reconciled."""
        if self.held:
            raise ValueError(f"{len(self.held)} series need identity or metadata review")
        return self.series


def plan_tv_views(
    arr_series: tuple[ArrSeries, ...], kodi_series: tuple[KodiSeries, ...], now: datetime,
) -> TvViewPlan:
    """Classify seasons, holding ambiguous or missing show identities."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must have a timezone")
    arr_ids = Counter(show.arr_id for show in arr_series)
    kodi_ids = Counter(show.kodi_id for show in kodi_series)
    arr_provider_ids = Counter(show.tvdb_id for show in arr_series if show.tvdb_id)
    kodi_provider_ids = Counter(show.tvdb_id for show in kodi_series if show.tvdb_id)
    kodi_by_provider = {show.tvdb_id: show for show in kodi_series if show.tvdb_id}
    matched_titles = Counter(
        kodi_by_provider[show.tvdb_id].display_title.strip().casefold()
        for show in arr_series
        if show.tvdb_id and arr_provider_ids[show.tvdb_id] == 1
        and kodi_provider_ids[show.tvdb_id] == 1
    )
    views: list[SeriesView] = []
    held: list[HeldSeries] = []
    skipped_empty: list[int] = []
    for show in arr_series:
        if not any(season.files for season in show.seasons):
            # A monitored but missing series has nothing for Kodi to display.
            skipped_empty.append(show.arr_id)
            continue
        reason: str | None = None
        if show.arr_id <= 0 or arr_ids[show.arr_id] != 1:
            reason = "invalid or duplicate ARR series ID"
        elif not show.tvdb_id:
            reason = "missing TVDB ID"
        elif arr_provider_ids[show.tvdb_id] != 1:
            reason = "duplicate ARR TVDB ID"
        elif kodi_provider_ids[show.tvdb_id] != 1:
            reason = "missing or duplicate Kodi TVDB ID"
        else:
            kodi = kodi_by_provider[show.tvdb_id]
            title = kodi.display_title.strip()
            if kodi.kodi_id <= 0 or kodi_ids[kodi.kodi_id] != 1 or not title:
                reason = "invalid or duplicate Kodi identity"
            elif matched_titles[title.casefold()] != 1:
                reason = "duplicate Kodi display title"
        season_numbers = [season.number for season in show.seasons]
        if reason is None and (any(number < 0 for number in season_numbers)
                               or len(set(season_numbers)) != len(season_numbers)):
            reason = "invalid or duplicate season number"
        if reason:
            held.append(HeldSeries(show.arr_id, reason))
            continue
        kodi = kodi_by_provider[show.tvdb_id]
        seasons = tuple(
            SeasonView(season.number, age_size_eligibility(season.files, now).eligible)
            for season in show.seasons
        )
        views.append(SeriesView(kodi.kodi_id, kodi.display_title.strip(), seasons))
    return TvViewPlan(tuple(views), tuple(held), tuple(skipped_empty))
