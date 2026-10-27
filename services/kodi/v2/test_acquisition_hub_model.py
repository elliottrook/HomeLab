import json
import unittest
from datetime import datetime, timezone

from acquisition_hub_model import (HubUnavailable, activate, build, complete,
                                   domain_state, move, request)
from landing_recommendations import parse_feed


NOW = datetime(2026, 10, 26, 18, tzinfo=timezone.utc)


def feed(domain, media_type, identity, title="Candidate"):
    payload = {"schema": 1, "generated_at": "2026-10-26T17:59:00Z",
               "items": [{"identity": identity, "media_type": media_type,
                           "title": title, "year": "2026", "overview": "Summary",
                           "poster": "https://example.invalid/poster.jpg",
                           "backdrop": "https://example.invalid/backdrop.jpg",
                           "explanation": "Because you may enjoy it.",
                           "owned": False, "archived": False,
                           "request_state": "none", "primary_action": "request",
                           "progress": 0.0}]}
    return parse_feed(json.dumps(payload).encode(), domain, NOW)


class AcquisitionHubModelTests(unittest.TestCase):
    def setUp(self):
        self.media = domain_state("media", feed(
            "media", "movie", "seerr:movie:41"), "live")
        self.music = domain_state("music", feed(
            "music", "album",
            "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc"),
            "cache")
        self.books = domain_state("books", feed(
            "books", "ebook", "openlibrary:/works/OL123W"), "live")
        self.state = build((self.media, self.music, self.books))

    def test_domains_preserve_focus_and_report_cached_source(self):
        music = activate(self.state, "music")
        self.assertEqual(music.item.media_type, "album")
        self.assertIn("six hours", music.status)
        self.assertEqual(activate(music, "media").item.identity,
                         "seerr:movie:41")

    def test_empty_and_unavailable_are_truthful_and_non_requestable(self):
        state = build((domain_state("media"),
                       domain_state("music", feed(
                           "music", "album",
                           "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc"),
                           "live"), domain_state("books")))
        self.assertIn("local libraries still work", state.status)
        with self.assertRaisesRegex(HubUnavailable, "acquisition-no-item"):
            request(state)

    def test_request_is_two_step_and_routes_by_authority_domain(self):
        first, proposal = request(self.state)
        self.assertEqual((first.phase, proposal.route, proposal.state),
                         ("confirm", "seerr", "confirm"))
        second, proposal = request(first, True)
        self.assertEqual((second.phase, proposal.state), ("submitting", "ready"))
        done = complete(second, proposal,
                        {"identity": proposal.identity, "status": "pending"})
        self.assertEqual(done.status, "Request awaiting approval")
        for domain, route in (("music", "music"), ("books", "books")):
            candidate, proposal = request(activate(self.state, domain))
            self.assertEqual(proposal.route, route)
            self.assertEqual(candidate.phase, "confirm")

    def test_result_must_correlate_and_uncertain_state_is_not_accepted(self):
        first, _ = request(self.state)
        second, proposal = request(first, True)
        for result in ({"identity": "seerr:movie:42", "status": "pending"},
                       {"identity": proposal.identity, "status": "uncertain"},
                       {"identity": proposal.identity, "status": "declined"}):
            with self.assertRaisesRegex(HubUnavailable, "acquisition-result"):
                complete(second, proposal, result)

    def test_navigation_clamps_and_cancels_confirmation(self):
        first, _ = request(self.state)
        moved = move(first, 1)
        self.assertEqual((moved.page.selected, moved.phase), (0, "browse"))

    def test_mixed_or_owned_feed_is_rejected(self):
        owned = list(self.media.items)
        owned[0] = owned[0].__class__(**dict(owned[0].__dict__, owned=True,
                                             primary_action="play"))
        altered = self.media.__class__("media", tuple(owned), "live", 0)
        # The constructor is intentionally simple; build cannot make an unsafe
        # state requestable because request re-checks the item boundary.
        state = build((altered, self.music, self.books))
        with self.assertRaisesRegex(HubUnavailable, "acquisition-not-requestable"):
            request(state)


if __name__ == "__main__":
    unittest.main()
