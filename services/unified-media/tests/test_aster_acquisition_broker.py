import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aster_acquisition_broker import (AcquisitionBroker, AuthorityResolution,
                                      BrokerError)


ALBUM_ID = "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc"
BOOK_ID = "openlibrary:/works/OL123W"


def request(identity=ALBUM_ID, media_type="album"):
    return {"schema": 1, "candidate_id": identity,
            "media_type": media_type, "confirm": True}


def feed(domain, identity=ALBUM_ID, media_type="album"):
    return {"schema": 1, "generated_at": "2026-10-26T18:00:00Z",
            "items": [{"identity": identity, "media_type": media_type,
                       "owned": False, "archived": False,
                       "request_state": "none", "primary_action": "request"}]}


class AcquisitionBrokerTests(unittest.TestCase):
    def broker(self, *, source=None, resolutions=None, writers=None):
        source = source or {"music": feed("music"),
                            "books": feed("books", BOOK_ID, "ebook")}
        resolutions = resolutions or {
            kind: (lambda command: AuthorityResolution(
                command.identity, "requestable", {"exact": command.authority_id}))
            for kind in ("album", "ebook", "audiobook")}
        writers = writers or {
            kind: (lambda _command, _payload: {"status": "pending",
                                                "request_id": "request-1"})
            for kind in ("album", "ebook", "audiobook")}
        return AcquisitionBroker(
            Path("/feeds"), resolutions, writers,
            feed_reader=lambda _root, domain: source[domain])

    def test_exact_candidate_is_revalidated_then_written_and_sanitized(self):
        calls = []
        resolutions = {
            kind: (lambda command, kind=kind: calls.append(("read", kind,
                    command.identity)) or AuthorityResolution(
                        command.identity, "requestable", {"opaque": kind}))
            for kind in ("album", "ebook", "audiobook")}
        writers = {
            kind: (lambda command, payload, kind=kind: calls.append(
                ("write", kind, command.identity, payload)) or
                {"status": "processing", "request_id": 42})
            for kind in ("album", "ebook", "audiobook")}
        value = self.broker(resolutions=resolutions, writers=writers).submit(request())
        self.assertEqual(value, {"schema": 1, "identity": ALBUM_ID,
                                 "status": "processing", "request_id": 42})
        self.assertEqual(calls[0], ("read", "album", ALBUM_ID))
        self.assertEqual(calls[1][0:3], ("write", "album", ALBUM_ID))

    def test_available_candidate_returns_without_writer(self):
        writes = []
        resolutions = {
            kind: (lambda command: AuthorityResolution(command.identity,
                                                        "available"))
            for kind in ("album", "ebook", "audiobook")}
        writers = {kind: (lambda *_args: writes.append(kind))
                   for kind in ("album", "ebook", "audiobook")}
        value = self.broker(resolutions=resolutions, writers=writers).submit(request())
        self.assertEqual(value["status"], "available")
        self.assertIsNone(value["request_id"])
        self.assertEqual(writes, [])

    def test_stale_or_changed_candidate_never_reaches_authority(self):
        calls = []
        source = {"music": feed("music", BOOK_ID, "album"),
                  "books": feed("books", BOOK_ID, "ebook")}
        broker = self.broker(source=source,
                             resolutions={kind: lambda _command: calls.append(1)
                                          for kind in ("album", "ebook", "audiobook")})
        with self.assertRaisesRegex(BrokerError,
                                    "acquisition-candidate-unavailable"):
            broker.submit(request())
        self.assertEqual(calls, [])

    def test_identity_mismatch_block_and_malformed_result_fail_closed(self):
        cases = (
            (AuthorityResolution("wrong", "requestable"),
             "acquisition-revalidation-invalid"),
            (AuthorityResolution(ALBUM_ID, "blocked"),
             "acquisition-candidate-unavailable"),
        )
        for resolution, error in cases:
            with self.subTest(error=error):
                resolutions = {kind: (lambda _command, value=resolution: value)
                               for kind in ("album", "ebook", "audiobook")}
                with self.assertRaisesRegex(BrokerError, error):
                    self.broker(resolutions=resolutions).submit(request())
        writers = {kind: (lambda *_args: {"status": "declined",
                                           "request_id": "private"})
                   for kind in ("album", "ebook", "audiobook")}
        with self.assertRaisesRegex(BrokerError,
                                    "acquisition-write-result-invalid"):
            self.broker(writers=writers).submit(request())

    def test_writer_failure_is_reported_uncertain_and_not_retried_here(self):
        calls = []
        def fail(*_args):
            calls.append(1)
            raise TimeoutError("provider may have accepted")
        writers = {kind: fail for kind in ("album", "ebook", "audiobook")}
        with self.assertRaisesRegex(BrokerError,
                                    "acquisition-write-outcome-uncertain"):
            self.broker(writers=writers).submit(request())
        self.assertEqual(calls, [1])

    def test_capability_map_must_be_exact(self):
        with self.assertRaisesRegex(BrokerError,
                                    "acquisition-broker-capabilities-invalid"):
            AcquisitionBroker(Path("/feeds"), {}, {}, feed_reader=lambda *_: {})


if __name__ == "__main__":
    unittest.main()
