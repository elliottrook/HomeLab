from datetime import datetime, timezone
import json
import unittest

from landing_recommendations import HeroState, hero_item, parse_feed


NOW = datetime(2026, 10, 26, 18, 0, tzinfo=timezone.utc)


def item(kind="movie", identity="seerr:movie:123", owned=False, progress=0.0,
         state="none", action=None):
    if action is None:
        action = "resume" if progress else ("play" if owned else "request")
    return {
        "identity": identity, "media_type": kind, "title": "Example",
        "year": "2026", "overview": "A synthetic recommendation.",
        "poster": "/poster.jpg", "backdrop": "/backdrop.jpg",
        "explanation": "Suggested from the bounded household snapshot.",
        "owned": owned, "archived": False, "request_state": state,
        "primary_action": action, "progress": progress,
    }


def feed(items):
    return json.dumps({"schema": 1, "generated_at": "2026-10-26T17:59:00Z",
                       "items": items}).encode()


class LandingRecommendationTests(unittest.TestCase):
    def test_domain_contract_never_crosses_media_types(self):
        cases = (("media", item()),
                 ("music", item(
                     "album",
                     "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc")),
                 ("books", item("ebook", "openlibrary:/works/OL1W")),
                 ("books", item("audiobook", "openlibrary:/works/OL2W")))
        for domain, value in cases:
            with self.subTest(domain=domain, kind=value["media_type"]):
                self.assertEqual(parse_feed(feed([value]), domain, NOW).items[0].media_type,
                                 value["media_type"])
        with self.assertRaisesRegex(ValueError, "landing-item-identity"):
            parse_feed(feed([item("album", "musicbrainz:abc")]), "media", NOW)
        with self.assertRaisesRegex(ValueError, "landing-item-identity"):
            parse_feed(feed([item("tv", "seerr:movie:123")]), "media", NOW)

    def test_owned_resume_and_unowned_request_are_exact(self):
        owned = item(owned=True, progress=0.42, state="available")
        parsed = parse_feed(feed([owned]), "media", NOW).items[0]
        self.assertEqual((parsed.primary_action, parsed.progress), ("resume", 0.42))
        unowned = parse_feed(feed([item()]), "media", NOW).items[0]
        self.assertEqual(unowned.primary_action, "request")
        for change in ({"primary_action": "request", "owned": True},
                       {"primary_action": "play", "progress": 0.4, "owned": True},
                       {"request_state": "pending", "primary_action": "request"}):
            broken = item(); broken.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                parse_feed(feed([broken]), "media", NOW)

    def test_stale_future_oversize_duplicate_and_extra_fields_fail_closed(self):
        stale = json.dumps({"schema": 1, "generated_at": "2026-10-26T01:00:00Z",
                            "items": [item()]}).encode()
        with self.assertRaisesRegex(ValueError, "landing-feed-stale"):
            parse_feed(stale, "media", NOW)
        future = json.dumps({"schema": 1, "generated_at": "2026-10-26T18:02:00Z",
                             "items": [item()]}).encode()
        with self.assertRaisesRegex(ValueError, "landing-feed-stale"):
            parse_feed(future, "media", NOW)
        with self.assertRaisesRegex(ValueError, "landing-feed-duplicate"):
            parse_feed(feed([item(), item()]), "media", NOW)
        extra = item(); extra["token"] = "never"
        with self.assertRaisesRegex(ValueError, "landing-item-schema"):
            parse_feed(feed([extra]), "media", NOW)
        with self.assertRaisesRegex(ValueError, "landing-feed-input"):
            parse_feed(b"x" * (256 * 1024 + 1), "media", NOW)

    def test_focus_is_authoritative_and_rotation_never_moves_it(self):
        first = item(identity="seerr:movie:1")
        second = item(identity="seerr:movie:2"); second["title"] = "Second"
        parsed = parse_feed(feed([first, second]), "media", NOW)
        state = HeroState(parsed, 100.0, interval=12.0)
        self.assertEqual(state.visible.identity, "seerr:movie:1")
        focused = hero_item(dict(first, identity="seerr:movie:99", title="Focused"), "media")
        state.focus(focused, 105.0)
        self.assertEqual(state.tick(200.0).identity, "seerr:movie:99")
        self.assertIs(state.focused, focused)
        state.clear_focus(201.0)
        self.assertEqual(state.visible.identity, "seerr:movie:1")
        self.assertEqual(state.tick(212.9).identity, "seerr:movie:1")
        self.assertEqual(state.tick(213.0).identity, "seerr:movie:2")
        self.assertIsNone(state.focused)

    def test_empty_domain_is_truthful_not_fabricated(self):
        parsed = parse_feed(feed([]), "music", NOW)
        state = HeroState(parsed, 0.0)
        self.assertIsNone(state.visible)
        self.assertIsNone(state.tick(120.0))

    def test_schema_identity_and_text_are_bounded(self):
        failures = []
        value = item(); value["identity"] = "seerr:../../secret"; failures.append(value)
        value = item(); value["year"] = "26"; failures.append(value)
        value = item(); value["title"] = ""; failures.append(value)
        value = item(); value["owned"] = 1; failures.append(value)
        value = item(); value["progress"] = 2.0; failures.append(value)
        value = item(); value["archived"] = True; value["owned"] = True; failures.append(value)
        for value in failures:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_feed(feed([value]), "media", NOW)


if __name__ == "__main__":
    unittest.main()
