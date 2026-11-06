"""Safety behavior for the dry-run retention selector."""

from dataclasses import replace
from datetime import date, datetime, timezone
from unittest import TestCase

from video_archiver.retention_policy import MediaUnit, UserWatch, plan_retention


NOW = datetime(2026, 11, 6, 20, tzinfo=timezone.utc)
USERS = frozenset({"member-a", "member-b"})


def movie(provider_id: str, year: int, **overrides) -> MediaUnit:
    facts = MediaUnit(
        provider_id=provider_id,
        kind="movie",
        file_count=1,
        current_file_imports=(),
        first_acquired_at=None,
        fallback_media_date=date(year, 1, 1),
        fallback_date_source="movie-release",
        fallback_date_precision="year",
        legacy_archive_unchanged=True,
        archive_view_verified=True,
        arr_file_matches=1,
        jellyfin_file_matches=1,
        watch=(UserWatch("member-a"), UserWatch("member-b")),
        subtitle_manifest_verified=True,
        recovery_ready=True,
        estimated_pool_reclaim_bytes=15,
    )
    return replace(facts, **overrides)


def plan(*units: MediaUnit, allocated=70):
    return plan_retention(
        units, now=NOW, expected_user_ids=USERS,
        pool_size_bytes=100, pool_allocated_bytes=allocated,
    )


class RetentionSafetyTests(TestCase):
    def test_no_candidates_below_sixty_percent(self):
        result = plan(movie("film-a", 1950), allocated=59)
        self.assertFalse(result.triggered)
        self.assertEqual(result.selected_provider_ids, ())

    def test_release_date_orders_legacy_without_claiming_acquisition(self):
        result = plan(movie("recent", 2000), movie("old", 1950))
        self.assertEqual(result.selected_provider_ids, ("old",))
        self.assertEqual(result.predicted_allocated_bytes, 55)
        self.assertEqual(result.remaining_to_target_bytes, 0)

    def test_known_acquisition_date_takes_precedence_over_fallback(self):
        unit = movie("known", 1950, first_acquired_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        result = plan(unit, movie("unknown", 2000), allocated=90)
        self.assertEqual(result.selected_provider_ids, ("unknown", "known"))

    def test_partial_watch_and_missing_user_hold(self):
        partial = movie("partial", 1950, watch=(UserWatch("member-a", progress_ticks=1), UserWatch("member-b")))
        missing = movie("missing", 1960, watch=(UserWatch("member-a"),))
        last_played = movie("last-played", 1970, watch=(
            UserWatch("member-a", last_played_at=NOW), UserWatch("member-b"),
        ))
        result = plan(partial, missing, last_played)
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual({h.provider_id for h in result.held}, {"partial", "missing", "last-played"})
        self.assertEqual(result.remaining_to_target_bytes, 10)

    def test_identity_recovery_and_missing_media_date_hold(self):
        units = (
            movie("path", 1950, jellyfin_file_matches=0),
            movie("recovery", 1950, recovery_ready=False),
            movie("date", 1950, fallback_media_date=None),
            movie("duplicate", 1950), movie("duplicate", 1950),
        )
        result = plan(*units)
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual(len(result.held), 4)

    def test_new_import_does_not_inherit_legacy_age(self):
        imported = movie(
            "new", 1950, legacy_archive_unchanged=False,
            current_file_imports=(datetime(2026, 10, 1, tzinfo=timezone.utc),),
        )
        result = plan(imported)
        self.assertEqual(result.selected_provider_ids, ())
        self.assertIn("three calendar months", result.held[0].reason)

    def test_whole_season_youngest_episode_controls_age(self):
        season = movie(
            "series-s1", 1950, kind="season", file_count=2,
            current_file_imports=(
                datetime(2026, 5, 1, tzinfo=timezone.utc),
                datetime(2026, 10, 1, tzinfo=timezone.utc),
            ),
            first_acquired_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            fallback_media_date=date(1950, 1, 1), fallback_date_source="season-air",
            legacy_archive_unchanged=False, arr_file_matches=2, jellyfin_file_matches=2,
        )
        self.assertEqual(plan(season).selected_provider_ids, ())
        old = replace(season, current_file_imports=(
            datetime(2026, 5, 1, tzinfo=timezone.utc),
            datetime(2026, 7, 1, tzinfo=timezone.utc),
        ))
        self.assertEqual(plan(old).selected_provider_ids, ("series-s1",))

    def test_guardrail_and_insufficient_safe_reclaim(self):
        result = plan(movie("only", 1950, estimated_pool_reclaim_bytes=2), allocated=63)
        self.assertTrue(result.upper_guardrail_exceeded)
        self.assertEqual(result.remaining_to_target_bytes, 1)

    def test_snapshot_held_space_and_rerequest_cooldown_hold(self):
        no_reclaim = movie("snapshot", 1950, estimated_pool_reclaim_bytes=0)
        cooldown = movie("rerequested", 1951, cooldown_until=datetime(2027, 1, 1, tzinfo=timezone.utc))
        result = plan(no_reclaim, cooldown, allocated=63)
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual(result.remaining_to_target_bytes, 3)
        self.assertEqual({h.reason for h in result.held}, {
            "pool reclaim estimate unavailable", "re-request cooldown active",
        })

    def test_year_only_date_cannot_claim_day_precision(self):
        invalid = movie("bad", 1950, fallback_media_date=date(1950, 6, 1))
        self.assertEqual(plan(invalid).selected_provider_ids, ())
