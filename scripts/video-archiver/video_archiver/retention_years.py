"""Conservative movie-year counts for retention planning.

The caller must enumerate every indexed household movie. Only distinct,
physically present, provider-verified titles visible to every expected user
contribute to a year. Excluding uncertain rows can hold more movies; it cannot
make the planner delete the last verified representative of a year.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MovieYearFact:
    provider_id: str | None
    release_year: int | None
    jellyfin_item_id: str
    path: str
    physical_present: bool
    arr_identity_verified: bool
    visible_user_ids: frozenset[str]


@dataclass(frozen=True)
class MovieYearInventory:
    counts: dict[int, int]
    examined: int
    counted: int
    held: int
    complete_source_scan: bool
    certified_facts: tuple[MovieYearFact, ...] = ()


def count_verified_movie_years(
    facts: tuple[MovieYearFact, ...], *, expected_user_ids: frozenset[str],
    source_scan_complete: bool, today: date,
) -> MovieYearInventory:
    """Return a lower-bound count of unique, available movies by release year.

    If the upstream listing or household roster is incomplete, no year may be
    certified. Duplicate provider IDs or paths invalidate every conflicting
    row, so alternate copies never count as separate films.
    """
    if not source_scan_complete or not expected_user_ids:
        return MovieYearInventory({}, len(facts), 0, len(facts), False)
    provider_counts = Counter(row.provider_id for row in facts if row.provider_id)
    path_counts = Counter(row.path for row in facts if row.path)
    item_counts = Counter(row.jellyfin_item_id for row in facts if row.jellyfin_item_id)
    years: Counter[int] = Counter()
    certified: list[MovieYearFact] = []
    for row in facts:
        if (
            not row.provider_id or provider_counts[row.provider_id] != 1
            or not row.jellyfin_item_id or item_counts[row.jellyfin_item_id] != 1
            or not row.path.startswith("/") or path_counts[row.path] != 1
            or not row.physical_present or not row.arr_identity_verified
            or row.visible_user_ids != expected_user_ids
            or type(row.release_year) is not int
            or not 1878 <= row.release_year <= today.year
        ):
            continue
        years[row.release_year] += 1
        certified.append(row)
    counted = len(certified)
    return MovieYearInventory(dict(years), len(facts), counted, len(facts) - counted,
                              True, tuple(certified))
