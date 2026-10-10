import unittest

from request_contract import Candidate, idempotency_key, plan_action


class RequestContractTests(unittest.TestCase):
    def test_dry_run_requires_explicit_approval(self):
        candidate = Candidate("music", "lidarr", "mbid-1", "Album", ("MusicBrainz match",))
        plan = plan_action(candidate)
        self.assertFalse(plan["approved"])
        self.assertIn("explicit_approval_required", plan["reasons"])

    def test_approved_unambiguous_candidate_is_ready(self):
        candidate = Candidate("tv", "seerr", "tmdb-1", "Show", ("TMDB exact match",))
        plan = plan_action(candidate, approve=True)
        self.assertTrue(plan["approved"])
        self.assertEqual(len(plan["idempotency_key"]), 64)

    def test_ambiguous_owned_and_archived_items_are_blocked(self):
        candidate = Candidate("ebook", "lazylibrarian", "isbn-1", "Book", (), 2, True, True)
        plan = plan_action(candidate, approve=True)
        self.assertFalse(plan["approved"])
        self.assertEqual(
            plan["reasons"],
            ["ambiguous_match", "already_owned", "archived_item", "missing_evidence"],
        )

    def test_idempotency_key_is_stable(self):
        candidate = Candidate("audio", "lazylibrarian", "isbn-2", "Book", ("exact",))
        self.assertEqual(idempotency_key(candidate), idempotency_key(candidate))


if __name__ == "__main__":
    unittest.main()
