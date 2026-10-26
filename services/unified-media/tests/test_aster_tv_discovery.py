import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aster_tv_discovery import (DiscoveryFeedError, build_feeds, read_feed,
                                write_feeds)


STAMP = "2026-10-26T22:00:00Z"


def row(kind="movie", authority="seerr", authority_id="123"):
    return {"media_type": kind, "authority": authority,
            "authority_id": authority_id, "title": "Example", "year": "2026",
            "overview": "Synopsis", "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg", "explanation": "Because.",
            "owned": False, "archived": False}


class AsterTVDiscoveryTests(unittest.TestCase):
    def test_builds_three_strict_domain_feeds(self):
        music = row("album", "musicbrainz",
                    "12345678-1234-1234-1234-123456789abc")
        music.update(poster_path="https://coverartarchive.org/release/a.jpg",
                     backdrop_path="")
        book = row("ebook", "openlibrary", "/works/OL123W")
        book.update(poster_path="https://covers.openlibrary.org/b/id/1-M.jpg",
                    backdrop_path="")
        feeds, stats = build_feeds([row(), music, book], STAMP)
        self.assertEqual(stats, {"invalid": 0, "duplicate": 0,
                                 "over_limit": 0})
        self.assertEqual(feeds["media"]["items"][0]["identity"],
                         "seerr:movie:123")
        self.assertEqual(feeds["music"]["items"][0]["identity"],
                         "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc")
        self.assertEqual(feeds["books"]["items"][0]["identity"],
                         "openlibrary:/works/OL123W")
        self.assertEqual(feeds["media"]["items"][0]["poster"],
                         "https://image.tmdb.org/t/p/w500/poster.jpg")

    def test_unsafe_and_duplicate_rows_are_omitted(self):
        bad = row(authority_id="../../secret")
        owned = row(authority_id="124"); owned["owned"] = True
        duplicate = row()
        feeds, stats = build_feeds([row(), bad, owned, duplicate], STAMP)
        self.assertEqual(len(feeds["media"]["items"]), 1)
        self.assertEqual(stats, {"invalid": 2, "duplicate": 1,
                                 "over_limit": 0})

    def test_write_and_read_are_atomic_and_bounded(self):
        feeds, _ = build_feeds([row()], STAMP)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_feeds(root, feeds)
            self.assertEqual(read_feed(root, "media"), feeds["media"])
            self.assertEqual(read_feed(root, "music")["items"], [])
            self.assertFalse(any(path.name.startswith(".") for path in root.iterdir()))

    def test_contract_rejects_bad_time_images_and_domains(self):
        with self.assertRaises(DiscoveryFeedError):
            build_feeds([row()], "yesterday")
        unsafe = row(); unsafe["poster_path"] = "http://example.invalid/a.jpg"
        feeds, stats = build_feeds([unsafe], STAMP)
        self.assertEqual(feeds["media"]["items"], [])
        self.assertEqual(stats["invalid"], 1)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "aster-tv-discovery-media.json"
            path.write_text(json.dumps({"schema": 1, "generated_at": STAMP,
                                        "items": [], "token": "never"}))
            with self.assertRaises(DiscoveryFeedError):
                read_feed(Path(temporary), "media")
            with self.assertRaises(DiscoveryFeedError):
                read_feed(Path(temporary), "video")

    def test_read_rejects_tampered_item(self):
        feeds, _ = build_feeds([row()], STAMP)
        feeds["media"]["items"][0]["owned"] = True
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for domain, value in feeds.items():
                (root / f"aster-tv-discovery-{domain}.json").write_text(json.dumps(value))
            with self.assertRaises(DiscoveryFeedError):
                read_feed(root, "media")


if __name__ == "__main__":
    unittest.main()
