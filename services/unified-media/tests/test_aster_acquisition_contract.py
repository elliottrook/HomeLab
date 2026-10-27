import copy
import unittest

from aster_acquisition_contract import (ContractError, proposal, resolve,
                                        response)


ALBUM = "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc"
BOOK = "openlibrary:/works/OL123W"


def item(identity=ALBUM, media_type="album"):
    return {"identity": identity, "media_type": media_type,
            "title": "Candidate", "year": "2026", "overview": "",
            "poster": "", "backdrop": "", "explanation": "",
            "owned": False, "archived": False, "request_state": "none",
            "primary_action": "request", "progress": 0.0}


def feed(value):
    return {"schema": 1, "generated_at": "2026-10-26T18:00:00Z",
            "items": [value]}


def body(identity=ALBUM, media_type="album"):
    return {"schema": 1, "candidate_id": identity,
            "media_type": media_type, "confirm": True}


class AsterAcquisitionContractTests(unittest.TestCase):
    def test_resolves_exact_album_and_book_authority(self):
        album = resolve(feed(item()), body())
        self.assertEqual((album.domain, album.authority, album.authority_id),
                         ("music", "musicbrainz",
                          "12345678-1234-1234-1234-123456789abc"))
        book = resolve(feed(item(BOOK, "ebook")), body(BOOK, "ebook"))
        self.assertEqual((book.domain, book.authority, book.authority_id),
                         ("books", "openlibrary", "/works/OL123W"))

    def test_refuses_media_and_unconfirmed_or_extra_fields(self):
        for value in (
                {"schema": 1, "candidate_id": "seerr:movie:41",
                 "media_type": "movie", "confirm": True},
                dict(body(), confirm=False),
                dict(body(), title="Candidate")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ContractError,
                                            "acquisition-proposal-invalid"):
                    proposal(value)

    def test_feed_identity_and_state_are_revalidated(self):
        base = item()
        variants = [dict(base, owned=True, primary_action="play"),
                    dict(base, archived=True),
                    dict(base, request_state="pending", primary_action="none"),
                    dict(base, media_type="ebook")]
        for value in variants:
            with self.subTest(value=value):
                with self.assertRaises(ContractError):
                    resolve(feed(value), body())
        with self.assertRaisesRegex(ContractError,
                                    "acquisition-candidate-unavailable"):
            resolve({"schema": 1, "generated_at": "x", "items": []}, body())

    def test_duplicate_identity_fails_closed(self):
        value = feed(item())
        value["items"].append(copy.deepcopy(value["items"][0]))
        with self.assertRaisesRegex(ContractError,
                                    "acquisition-candidate-unavailable"):
            resolve(value, body())

    def test_sanitized_response_correlates_identity(self):
        command = resolve(feed(item()), body())
        self.assertEqual(response(command, "pending", 41),
                         {"schema": 1, "identity": ALBUM,
                          "status": "pending", "request_id": 41})
        self.assertIsNone(response(command, "available", None)["request_id"])
        for status, request_id in (("available", 1), ("pending", None),
                                   ("declined", 1)):
            with self.assertRaisesRegex(ContractError,
                                        "acquisition-response-invalid"):
                response(command, status, request_id)

    def test_identity_shapes_are_strict(self):
        for identity, media_type in (("musicbrainz:release:123", "album"),
                                     ("openlibrary:/works/OL0W", "ebook"),
                                     ("openlibrary:/works/OL123W", "album")):
            with self.subTest(identity=identity):
                with self.assertRaisesRegex(ContractError,
                                            "acquisition-proposal-identity"):
                    proposal(body(identity, media_type))


if __name__ == "__main__":
    unittest.main()
