import json
import unittest
from datetime import datetime, timezone

from acquisition_hub_model import activate, build, domain_state, request
from acquisition_page_model import render
from landing_recommendations import parse_feed


NOW = datetime(2026, 10, 26, 18, tzinfo=timezone.utc)


def source(domain, media_type, identity):
    value = {"schema": 1, "generated_at": "2026-10-26T17:59:00Z",
             "items": [{"identity": identity, "media_type": media_type,
                         "title": "The Candidate", "year": "2026",
                         "overview": "A useful synopsis.",
                         "poster": "https://example.invalid/poster.jpg",
                         "backdrop": "https://example.invalid/backdrop.jpg",
                         "explanation": "Recommended by the private hub.",
                         "owned": False, "archived": False,
                         "request_state": "none", "primary_action": "request",
                         "progress": 0.0}]}
    return parse_feed(json.dumps(value).encode(), domain, NOW)


class AcquisitionPageModelTests(unittest.TestCase):
    def setUp(self):
        self.state = build((
            domain_state("media", source("media", "tv", "seerr:tv:41"), "live"),
            domain_state("music", source(
                "music", "album",
                "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc"), "cache"),
            domain_state("books", source(
                "books", "audiobook", "openlibrary:/works/OL123W"), "live")))

    def test_media_hands_off_to_seerr_and_projects_art(self):
        view = render(self.state)
        self.assertEqual((view.domain, view.action, view.title),
                         ("media", "Open Seerr", "The Candidate"))
        self.assertEqual(view.rows[0].label2, "Television · 2026")
        self.assertTrue(view.backdrop.startswith("https://"))

    def test_music_and_books_have_domain_specific_actions(self):
        music = render(activate(self.state, "music"))
        books = render(activate(self.state, "books"))
        self.assertEqual((music.action, books.action),
                         ("Request album", "Request book"))
        self.assertIn("six hours", music.status)

    def test_confirmation_is_visible_in_place(self):
        confirming, _ = request(activate(self.state, "books"))
        view = render(confirming)
        self.assertTrue(view.confirmation)
        self.assertEqual(view.action, "Confirm request book")

    def test_empty_page_is_truthful_and_has_no_action(self):
        state = build((domain_state("media"), domain_state("music"),
                       domain_state("books")))
        view = render(state)
        self.assertFalse(view.action_enabled)
        self.assertEqual(view.title, "Nothing to show yet")
        self.assertIn("local library", view.synopsis)


if __name__ == "__main__":
    unittest.main()
