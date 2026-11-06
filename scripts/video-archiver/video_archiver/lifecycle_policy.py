"""Age and byte-size rules for Current and Archive view candidates.

This module does not move or rewrite media. The caller must retain each file's
first-seen time and legacy classification when an optimizer replaces it.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


ARCHIVE_CEILING_BYTES = 5_000_000_000
ARCHIVE_AGE_MONTHS = 4


@dataclass(frozen=True)
class FileAgeSize:
    first_seen_at: datetime
    size_bytes: int
    # Set only from a one-time, verified baseline of an existing Archive root.
    # ARR's migration dateAdded is not the older file's original import time.
    legacy_archive_at_baseline: bool = False


@dataclass(frozen=True)
class Eligibility:
    eligible: bool
    reason: str


def calendar_months_before(instant: datetime, months: int) -> datetime:
    """Return the same local wall time, clamping the day at month end."""
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("instant must have a timezone")
    if months < 0:
        raise ValueError("months must be non-negative")
    month_index = instant.year * 12 + instant.month - 1 - months
    if month_index < 12:
        raise ValueError("date is too early for the requested month offset")
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(instant.day, calendar.monthrange(year, month)[1])
    return instant.replace(year=year, month=month, day=day)


def age_size_eligibility(
    files: Iterable[FileAgeSize], now: datetime,
    *, ceiling_bytes: int = ARCHIVE_CEILING_BYTES,
    age_months: int = ARCHIVE_AGE_MONTHS,
) -> Eligibility:
    """Check one movie file or all files in one TV season.

    The youngest original import of files added after the legacy baseline
    controls the season. Existing Archive files can be grandfathered because
    ARR's migration dateAdded does not reflect their true age. A file above the
    ceiling keeps the entire season in Current. Quality and subtitle checks
    are separate acceptance gates and must not be inferred from a pass here.
    """
    cutoff = calendar_months_before(now, age_months)
    if ceiling_bytes <= 0:
        raise ValueError("ceiling_bytes must be positive")
    records = list(files)
    if not records:
        return Eligibility(False, "no files")
    for record in records:
        if record.first_seen_at.tzinfo is None or record.first_seen_at.utcoffset() is None:
            return Eligibility(False, "missing import timezone")
        if record.size_bytes <= 0:
            return Eligibility(False, "missing or invalid file size")
        if record.size_bytes > ceiling_bytes:
            return Eligibility(False, "file exceeds Archive ceiling")
    newly_imported = [record.first_seen_at for record in records if not record.legacy_archive_at_baseline]
    if newly_imported and max(newly_imported) > cutoff:
        return Eligibility(False, f"youngest file is under {age_months} calendar months old")
    return Eligibility(True, "age and size pass")
