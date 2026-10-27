import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aster_acquisition_broker import BrokerError
from aster_acquisition_contract import Command
from aster_acquisition_providers import (LazyLibrarianProvider,
                                         LidarrProvider)


ALBUM_ID = "12345678-1234-1234-1234-123456789abc"


class Transport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, path, query, body):
        self.calls.append((method, path, query, body))
        return self.responses.pop(0)


def album():
    return Command("musicbrainz:release-group:" + ALBUM_ID, "album",
                   "music", "musicbrainz", ALBUM_ID, "Kind of Blue")


def book(kind="ebook"):
    return Command("openlibrary:/works/OL123W", kind, "books",
                   "openlibrary", "/works/OL123W", "Dune")


class LidarrProviderTests(unittest.TestCase):
    def provider(self, transport):
        return LidarrProvider(transport, root="/music", quality_profile_id=1,
                              metadata_profile_id=2)

    def test_revalidation_uses_exact_mbid_and_write_does_not_follow_artist(self):
        transport = Transport([
            (200, []),
            (200, [{"foreignAlbumId": ALBUM_ID, "title": "Kind of Blue",
                    "artist": {"foreignArtistId": "artist-1"}}]),
            (201, {"id": 41}),
        ])
        provider = self.provider(transport)
        current = provider.revalidate(album())
        self.assertEqual((current.identity, current.state),
                         (album().identity, "requestable"))
        result = provider.write(album(), current.payload)
        self.assertEqual(result, {"status": "processing", "request_id": 41})
        self.assertEqual(transport.calls[0][2], {"foreignAlbumId": ALBUM_ID})
        self.assertEqual(transport.calls[1][2], {"term": "Kind of Blue"})
        body = transport.calls[2][3]
        self.assertTrue(body["monitored"])
        self.assertFalse(body["artist"]["monitored"])
        self.assertEqual(body["artist"]["monitorNewItems"], "none")

    def test_existing_exact_album_is_available_without_lookup(self):
        transport = Transport([(200, [{"foreignAlbumId": ALBUM_ID}])])
        current = self.provider(transport).revalidate(album())
        self.assertEqual(current.state, "available")
        self.assertEqual(len(transport.calls), 1)

    def test_ambiguous_existing_or_lookup_fails_closed(self):
        for responses, error in (
            ([(200, [{"foreignAlbumId": "other"}])],
             "acquisition-lidarr-existing-ambiguous"),
            ([(200, []), (200, [
                {"foreignAlbumId": ALBUM_ID}, {"foreignAlbumId": ALBUM_ID}])],
             "acquisition-lidarr-match"),
        ):
            with self.subTest(error=error):
                with self.assertRaisesRegex(BrokerError, error):
                    self.provider(Transport(responses)).revalidate(album())


class LazyLibrarianProviderTests(unittest.TestCase):
    def test_ebook_and_audiobook_check_their_own_status(self):
        record = {"BookID": "OL123W", "BookName": "Dune",
                  "Status": "Have", "AudioStatus": "Skipped"}
        ebook = LazyLibrarianProvider(Transport([(200, [record])])).revalidate(
            book("ebook"))
        audio = LazyLibrarianProvider(Transport([(200, [record])])).revalidate(
            book("audiobook"))
        self.assertEqual((ebook.state, audio.state),
                         ("available", "requestable"))

    def test_book_write_adds_then_queues_exact_format(self):
        transport = Transport([(200, []), (200, True), (200, "OK")])
        provider = LazyLibrarianProvider(transport)
        current = provider.revalidate(book("audiobook"))
        result = provider.write(book("audiobook"), current.payload)
        self.assertEqual(result, {"status": "processing",
                                  "request_id": "OL123W"})
        self.assertEqual(transport.calls[1][2]["cmd"], "addBook")
        self.assertEqual(transport.calls[2][2]["type"], "AudioBook")

    def test_duplicate_or_title_change_fails_before_write(self):
        duplicate = [{"BookID": "OL123W", "BookName": "Dune"},
                     {"BookID": "/works/OL123W", "BookName": "Dune"}]
        for rows, error in ((duplicate, "acquisition-lazy-existing-ambiguous"),
                            ([{"BookID": "OL123W", "BookName": "Other"}],
                             "acquisition-lazy-identity-changed")):
            with self.subTest(error=error):
                with self.assertRaisesRegex(BrokerError, error):
                    LazyLibrarianProvider(Transport([(200, rows)])).revalidate(
                        book())


if __name__ == "__main__":
    unittest.main()
