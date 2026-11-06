"""Safety behavior for the dry-run retention selector."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from unittest import TestCase

from video_archiver.retention_policy import MediaUnit, UserWatch, plan_notice_proposals, plan_retention


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
        watch_evidence_complete=True,
        household_notice_at=NOW - timedelta(days=8),
        household_notice_identity_verified=True,
        movie_release_year=year,
    )
    return replace(facts, **overrides)


def plan(*units: MediaUnit, allocated=70, movie_year_counts=None):
    if movie_year_counts is None:
        movie_year_counts = {
            unit.movie_release_year: 2 for unit in units
            if unit.kind == "movie" and unit.movie_release_year is not None
        }
    return plan_retention(
        units, now=NOW, expected_user_ids=USERS,
        pool_size_bytes=100, pool_allocated_bytes=allocated,
        movie_year_counts=movie_year_counts,
    )


class RetentionSafetyTests(TestCase):
    def test_notice_proposal_cannot_be_used_as_deletion_eligibility(self):
        pending = movie("pending", 1950, household_notice_at=None,
                        household_notice_identity_verified=False)
        held = movie("kept", 1951, household_notice_at=None,
                     household_notice_identity_verified=False, household_keep=True)
        notices = plan_notice_proposals(
            (pending, held), now=NOW, expected_user_ids=USERS,
            pool_size_bytes=100, pool_allocated_bytes=70,
            movie_year_counts={1950: 2, 1951: 2},
        )
        deletion = plan(pending, held)
        self.assertEqual(notices.proposal_provider_ids, ("pending",))
        self.assertEqual(deletion.selected_provider_ids, ())

    def test_missing_recent_or_unbound_household_notice_holds(self):
        units = (
            movie("missing", 1950, household_notice_at=None),
            movie("recent", 1951, household_notice_at=NOW - timedelta(days=2)),
            movie("unbound", 1952, household_notice_identity_verified=False),
        )
        result = plan(*units)
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual({row.reason for row in result.held}, {
            "household notice or file identity unverified",
            "household notice grace period active",
        })

    def test_three_day_notice_boundary(self):
        just_ready = plan(movie("ready", 1950, household_notice_at=NOW - timedelta(days=3)))
        self.assertEqual(just_ready.selected_provider_ids, ("ready",))
        too_early = plan(movie("early", 1950, household_notice_at=NOW - timedelta(days=3) + timedelta(seconds=1)))
        self.assertEqual(too_early.selected_provider_ids, ())
        self.assertEqual(too_early.held[0].reason, "household notice grace period active")

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

    def test_currently_unwatched_legacy_file_stays_held_without_complete_evidence(self):
        result = plan(movie("legacy", 1950, watch_evidence_complete=False))
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual(result.held[0].reason, "current watch and retained playback evidence incomplete")

    def test_retained_playback_event_protects_even_after_userdata_reset(self):
        result = plan(movie("reset", 1950, historical_playback=True))
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual(result.held[0].reason, "retained playback log records a watch")

    def test_astertv_household_keep_blocks_unwatched_title(self):
        result = plan(movie("kept", 1950, household_keep=True))
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual(result.held[0].reason, "household Keep decision")

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

    def test_only_movie_from_year_is_held_even_when_other_years_can_be_deleted(self):
        result = plan(movie("sole", 1939), movie("other", 1940),
                      movie_year_counts={1939: 1, 1940: 2})
        self.assertEqual(result.selected_provider_ids, ("other",))
        self.assertIn(("sole", "last movie from release year"),
                      {(row.provider_id, row.reason) for row in result.held})

    def test_batch_never_removes_final_movie_from_same_year(self):
        result = plan(movie("first", 1939), movie("second", 1939),
                      allocated=90, movie_year_counts={1939: 2})
        self.assertEqual(len(result.selected_provider_ids), 1)
        self.assertEqual(result.remaining_to_target_bytes, 15)
        self.assertEqual(len([row for row in result.held if row.reason == "last movie from release year"]), 1)

    def test_missing_or_conflicting_year_inventory_holds_movie(self):
        self.assertEqual(plan(movie("missing", 1939), movie_year_counts={}).selected_provider_ids, ())
        self.assertEqual(plan(movie("bad-count", 1939), movie_year_counts={1939: 2.0}).selected_provider_ids, ())
        result = plan(movie("first", 1939), movie("second", 1939), movie_year_counts={1939: 1})
        self.assertEqual(result.selected_provider_ids, ())
        self.assertEqual({row.reason for row in result.held}, {"movie year inventory incomplete"})
