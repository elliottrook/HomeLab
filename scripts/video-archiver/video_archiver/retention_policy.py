"""Pure, dry-run Archive retention decisions. No filesystem or ARR writes.

Inputs must come from a fresh, source-local ARR/Jellyfin/TrueNAS reconciliation.
The planner predicts candidate order only; it never treats apparent file bytes
as proof that ZFS will release the same number of bytes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Mapping

from .lifecycle_policy import calendar_months_before


DateSource = Literal["acquired", "movie-release", "season-air", "series-air"]
DatePrecision = Literal["day", "year"]
Kind = Literal["movie", "season"]


@dataclass(frozen=True)
class UserWatch:
    user_id: str
    played: bool = False
    play_count: int = 0
    last_played_at: datetime | None = None
    progress_ticks: int = 0
    favorite: bool = False
    keep: bool = False

    @property
    def protected(self) -> bool:
        return (
            self.played or self.play_count > 0 or self.last_played_at is not None
            or self.progress_ticks > 0
            or self.favorite or self.keep
        )


@dataclass(frozen=True)
class MediaUnit:
    provider_id: str
    kind: Kind
    file_count: int
    current_file_imports: tuple[datetime, ...]
    first_acquired_at: datetime | None
    fallback_media_date: date | None
    fallback_date_source: DateSource | None
    fallback_date_precision: DatePrecision | None
    legacy_archive_unchanged: bool
    archive_view_verified: bool
    arr_file_matches: int
    jellyfin_file_matches: int
    watch: tuple[UserWatch, ...]
    subtitle_manifest_verified: bool
    recovery_ready: bool
    estimated_pool_reclaim_bytes: int
    watch_history_verified: bool = False
    movie_release_year: int | None = None
    has_identity_conflict: bool = False
    active_playback_or_download: bool = False
    cooldown_until: datetime | None = None


@dataclass(frozen=True)
class HeldUnit:
    provider_id: str
    reason: str


@dataclass(frozen=True)
class RetentionPlan:
    triggered: bool
    upper_guardrail_exceeded: bool
    selected_provider_ids: tuple[str, ...]
    held: tuple[HeldUnit, ...]
    predicted_allocated_bytes: int
    remaining_to_target_bytes: int


def _aware(value: datetime | None) -> bool:
    return value is not None and value.tzinfo is not None and value.utcoffset() is not None


def _candidate_date(unit: MediaUnit, now: datetime) -> tuple[date | None, str | None]:
    if unit.first_acquired_at is not None:
        if not _aware(unit.first_acquired_at) or unit.first_acquired_at > now:
            return None, "invalid first-acquisition date"
        return unit.first_acquired_at.date(), None
    source = unit.fallback_date_source
    if source not in ("movie-release", "season-air", "series-air"):
        return None, "missing acquisition and media-date provenance"
    if unit.kind == "movie" and source != "movie-release":
        return None, "wrong movie media-date source"
    if unit.kind == "season" and source == "movie-release":
        return None, "wrong season media-date source"
    media_date = unit.fallback_media_date
    if media_date is None or media_date.year < 1878 or media_date > now.date():
        return None, "invalid media-date fallback"
    if unit.fallback_date_precision not in ("day", "year"):
        return None, "missing media-date precision"
    if unit.fallback_date_precision == "year" and (media_date.month, media_date.day) != (1, 1):
        return None, "year-only date must use January 1"
    return media_date, None


def _hold_reason(
    unit: MediaUnit, now: datetime, expected_user_ids: frozenset[str],
) -> tuple[date | None, str | None]:
    if not unit.provider_id or unit.kind not in ("movie", "season"):
        return None, "invalid provider identity or media kind"
    if unit.file_count <= 0:
        return None, "no files"
    if unit.has_identity_conflict:
        return None, "identity or duplicate conflict"
    if not unit.archive_view_verified:
        return None, "Archive membership unverified"
    if unit.arr_file_matches != unit.file_count or unit.jellyfin_file_matches != unit.file_count:
        return None, "ARR/Jellyfin file ownership incomplete"
    if not unit.legacy_archive_unchanged:
        if len(unit.current_file_imports) != unit.file_count:
            return None, "current-file import dates incomplete"
        if any(not _aware(value) or value > now for value in unit.current_file_imports):
            return None, "invalid current-file import date"
        if max(unit.current_file_imports) > calendar_months_before(now, 3):
            return None, "younger than three calendar months"
    if not expected_user_ids or len(unit.watch) != len(expected_user_ids):
        return None, "household watch state incomplete"
    if not unit.watch_history_verified:
        return None, "watch history continuity unverified"
    watch_ids = [row.user_id for row in unit.watch]
    if len(set(watch_ids)) != len(watch_ids) or set(watch_ids) != expected_user_ids:
        return None, "household watch identities incomplete"
    if any(row.protected for row in unit.watch):
        return None, "watched, in progress, favorite or keep"
    if not unit.subtitle_manifest_verified:
        return None, "subtitle/sidecar manifest unverified"
    if unit.active_playback_or_download:
        return None, "active playback or download"
    if not unit.recovery_ready:
        return None, "recovery checkpoint unverified"
    if unit.cooldown_until is not None:
        if not _aware(unit.cooldown_until):
            return None, "invalid cooldown date"
        if unit.cooldown_until > now:
            return None, "re-request cooldown active"
    if unit.estimated_pool_reclaim_bytes <= 0:
        return None, "pool reclaim estimate unavailable"
    return _candidate_date(unit, now)


def plan_retention(
    units: tuple[MediaUnit, ...], *, now: datetime,
    expected_user_ids: frozenset[str], pool_size_bytes: int,
    pool_allocated_bytes: int, movie_year_counts: Mapping[int, int] | None = None,
) -> RetentionPlan:
    """Select oldest eligible units until predicted raw pool use returns to 60%.

    A caller must re-read actual ZFS allocation and all candidate facts after
    each bounded action. This projection never authorizes deletion by itself.
    """
    if not _aware(now):
        raise ValueError("now must be timezone aware")
    if pool_size_bytes <= 0 or not 0 <= pool_allocated_bytes <= pool_size_bytes:
        raise ValueError("invalid pool accounting")
    triggered = 100 * pool_allocated_bytes >= 60 * pool_size_bytes
    guardrail = 100 * pool_allocated_bytes >= 62 * pool_size_bytes
    target = 60 * pool_size_bytes // 100
    if not triggered:
        return RetentionPlan(False, guardrail, (), (), pool_allocated_bytes, 0)
    held: list[HeldUnit] = []
    eligible: list[tuple[date, str, MediaUnit]] = []
    # Counts must cover distinct, physically present movies in every household
    # movie library, including Current. Missing or conflicting evidence holds.
    remaining_by_year = {
        year: count for year, count in (movie_year_counts or {}).items()
        if type(year) is int and type(count) is int and 1878 <= year <= now.year and count > 0
    }
    candidate_year_counts = Counter(
        unit.movie_release_year for unit in units
        if unit.kind == "movie" and unit.movie_release_year is not None
    )
    seen_ids: set[str] = set()
    duplicate_ids = {provider_id for provider_id, count in Counter(u.provider_id for u in units).items() if count > 1}
    for unit in units:
        if unit.provider_id in seen_ids:
            continue
        seen_ids.add(unit.provider_id)
        if unit.provider_id in duplicate_ids:
            held.append(HeldUnit(unit.provider_id, "duplicate provider identity"))
            continue
        if unit.kind == "movie" and (
            unit.movie_release_year is None
            or not 1878 <= unit.movie_release_year <= now.year
            or remaining_by_year.get(unit.movie_release_year, 0) < candidate_year_counts[unit.movie_release_year]
        ):
            held.append(HeldUnit(unit.provider_id, "movie year inventory incomplete"))
            continue
        rank_date, reason = _hold_reason(unit, now, expected_user_ids)
        if reason:
            held.append(HeldUnit(unit.provider_id, reason))
        else:
            assert rank_date is not None
            eligible.append((rank_date, unit.provider_id, unit))
    eligible.sort(key=lambda item: (item[0], item[1]))
    selected: list[str] = []
    predicted = pool_allocated_bytes
    for _, _, unit in eligible:
        if predicted <= target:
            break
        if unit.kind == "movie":
            assert unit.movie_release_year is not None
            if remaining_by_year[unit.movie_release_year] <= 1:
                held.append(HeldUnit(unit.provider_id, "last movie from release year"))
                continue
            remaining_by_year[unit.movie_release_year] -= 1
        selected.append(unit.provider_id)
        predicted = max(0, predicted - unit.estimated_pool_reclaim_bytes)
    return RetentionPlan(
        True, guardrail, tuple(selected), tuple(held), predicted,
        max(0, predicted - target),
    )
