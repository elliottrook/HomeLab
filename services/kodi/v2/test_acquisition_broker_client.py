import json
from pathlib import Path
import tempfile
import unittest

from acquisition_broker_client import (AcquisitionUnavailable, RequestWriter,
                                       result, restore_saved_state)
from acquisition_hub_model import (RequestProposal, activate, build, domain_state,
                                   request)
from acquisition_page_model import render
from test_acquisition_page_model import source


class AcquisitionBrokerClientTests(unittest.TestCase):
    def proposal(self, route="music", identity=None, media_type="album"):
        identity = identity or (
            "musicbrainz:release-group:12345678-1234-1234-1234-123456789abc")
        return RequestProposal(identity, media_type, route, "ready")

    def test_commit_is_journalled_without_display_metadata_and_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            calls = []
            proposal = self.proposal()
            response = {"schema": 1, "identity": proposal.identity,
                        "status": "pending", "request_id": "lidarr-41"}
            writer = RequestWriter(temporary,
                                   {"music": lambda body: calls.append(body) or response})
            self.assertEqual(writer.submit(proposal), response)
            self.assertEqual(writer.submit(proposal), response)
            self.assertEqual(len(calls), 1)
            record = json.loads(next(Path(temporary).glob("*.json")).read_text())
            self.assertEqual(record["status"], "committed")
            self.assertNotIn("title", json.dumps(record).lower())
            self.assertEqual(Path(temporary).stat().st_mode & 0o777, 0o700)
            self.assertEqual(next(Path(temporary).glob("*.json")).stat().st_mode & 0o777,
                             0o600)

    def test_transport_failure_is_sticky_and_never_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            calls = []
            def fail(body):
                calls.append(body)
                raise OSError("private upstream detail")
            writer = RequestWriter(temporary, {"books": fail})
            proposal = self.proposal("books", "openlibrary:/works/OL123W",
                                     "ebook")
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-outcome-uncertain"):
                writer.submit(proposal)
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-recovery-required"):
                writer.submit(proposal)
            self.assertEqual(len(calls), 1)
            record = json.loads(next(Path(temporary).glob("*.json")).read_text())
            self.assertEqual(record["status"], "uncertain")
            self.assertNotIn("private upstream", json.dumps(record))

    def test_wrong_identity_and_invalid_status_become_uncertain(self):
        for response in (
                {"schema": 1, "identity": "wrong", "status": "pending",
                 "request_id": "1"},
                {"schema": 1, "identity": "openlibrary:/works/OL123W",
                 "status": "declined", "request_id": "1"}):
            with self.subTest(response=response):
                with tempfile.TemporaryDirectory() as temporary:
                    proposal = self.proposal("books",
                                             "openlibrary:/works/OL123W", "ebook")
                    writer = RequestWriter(temporary,
                                           {"books": lambda body: response})
                    with self.assertRaisesRegex(AcquisitionUnavailable,
                                                "acquisition-outcome-uncertain"):
                        writer.submit(proposal)

    def test_available_requires_no_request_id_and_pending_requires_one(self):
        proposal = self.proposal()
        self.assertEqual(result({"schema": 1, "identity": proposal.identity,
                                 "status": "available", "request_id": None},
                                proposal)["status"], "available")
        for response in (
                {"schema": 1, "identity": proposal.identity,
                 "status": "available", "request_id": "already"},
                {"schema": 1, "identity": proposal.identity,
                 "status": "pending", "request_id": None}):
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-result-invalid"):
                result(response, proposal)

    def test_absent_route_and_unconfirmed_proposal_do_not_create_journal(self):
        with tempfile.TemporaryDirectory() as temporary:
            ready = self.proposal()
            writer = RequestWriter(temporary, {})
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-route-unavailable"):
                writer.submit(ready)
            self.assertEqual(tuple(Path(temporary).iterdir()), ())
            confirm = RequestProposal(ready.identity, ready.media_type,
                                      ready.route, "confirm")
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-proposal-not-ready"):
                writer.submit(confirm)

    def test_generic_writer_refuses_media_route(self):
        proposal = RequestProposal("seerr:tv:41", "tv", "seerr", "ready")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-transports-invalid"):
                RequestWriter(temporary, {"seerr": lambda body: {}})
            writer = RequestWriter(temporary, {})
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-proposal-not-ready"):
                writer.submit(proposal)
            self.assertEqual(tuple(Path(temporary).iterdir()), ())

    def test_journal_filename_does_not_expose_candidate_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            proposal = self.proposal("books", "openlibrary:/works/OL123W",
                                     "ebook")
            response = {"schema": 1, "identity": proposal.identity,
                        "status": "pending", "request_id": 7}
            RequestWriter(temporary,
                          {"books": lambda body: response}).submit(proposal)
            name = next(Path(temporary).iterdir()).name
            self.assertRegex(name, r"^[0-9a-f]{64}\.json$")
            self.assertNotIn("openlibrary", name)

    def test_journal_root_is_private_and_linked_state_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "journal"
            root.mkdir(mode=0o755)
            writer = RequestWriter(root, {"music": lambda _body: {}})
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)
            proposal = self.proposal()
            target = Path(temporary) / "outside.json"
            target.write_text("{}")
            writer._path(proposal).symlink_to(target)
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-journal-invalid"):
                writer.submit(proposal)
            self.assertEqual(target.read_text(), "{}")

    def test_linked_journal_root_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "real"
            target.mkdir()
            linked = Path(temporary) / "linked"
            linked.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(AcquisitionUnavailable,
                                        "acquisition-journal-root-invalid"):
                RequestWriter(linked, {})

    def state(self, domain='music', kind='album', identity=None):
        identity = identity or self.proposal().identity
        return activate(build(domain_state(d, source(d, kind, identity), 'live')
                              if d == domain else domain_state(d)
                              for d in ('media', 'music', 'books')), domain)

    def test_reopen_restores_accepted_status_without_a_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            proposal = self.proposal()
            value = {'schema': 1, 'identity': proposal.identity,
                     'status': 'processing', 'request_id': 41}
            RequestWriter(temporary, {'music': lambda _: value}).submit(proposal)
            path = next(Path(temporary).glob('*.json'))
            before = path.read_bytes()
            view = render(restore_saved_state(self.state(), RequestWriter(temporary, {})))
            self.assertEqual(view.status, 'Request accepted · waiting for library import')
            self.assertFalse(view.action_enabled)
            self.assertEqual(before, path.read_bytes())

    def test_uncertain_reopen_blocks_action_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            calls = []
            def fail(_):
                calls.append(True)
                raise OSError('synthetic failure')
            writer = RequestWriter(temporary, {'music': fail})
            with self.assertRaises(AcquisitionUnavailable):
                writer.submit(self.proposal())
            state = restore_saved_state(self.state(), writer)
            self.assertEqual(state.phase, 'blocked')
            self.assertIn('no retry', render(state).status)
            self.assertFalse(render(state).action_enabled)
            self.assertEqual(calls, [True])

    def test_unrequested_confirmation_is_preserved_without_creating_a_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            state, _ = request(self.state())
            writer = RequestWriter(temporary, {})
            self.assertEqual(restore_saved_state(state, writer), state)
            self.assertIsNone(writer.saved(self.proposal()))
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_saved_ebook_outcome_cannot_be_used_for_audiobook(self):
        with tempfile.TemporaryDirectory() as temporary:
            identity = 'openlibrary:/works/OL123W'
            ebook = self.proposal('books', identity, 'ebook')
            value = {'schema': 1, 'identity': identity,
                     'status': 'processing', 'request_id': 'OL123W'}
            writer = RequestWriter(temporary, {'books': lambda _: value})
            writer.submit(ebook)
            state = restore_saved_state(self.state('books', 'audiobook', identity), writer)
            self.assertEqual(state.phase, 'blocked')
            self.assertFalse(render(state).action_enabled)

    def test_dangling_journal_link_is_refused_without_creating_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/'journal'
            writer = RequestWriter(root, {})
            target = Path(temporary)/'absent.json'
            writer._path(self.proposal()).symlink_to(target)
            with self.assertRaisesRegex(AcquisitionUnavailable, 'journal-invalid'):
                writer.saved(self.proposal())
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
