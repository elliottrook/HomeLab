import json
import sys
import tempfile
import unittest
from pathlib import Path

BROKER_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BROKER_ROOT))

from aster_games_broker.romm import RomMClient
from aster_games_broker.server import read_gate
from aster_games_broker.store import ProposalStore, ValidationError


class ProposalStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProposalStore(Path(self.temp.name) / "proposals.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def test_request_is_pending_and_content_silent(self):
        proposal, created = self.store.create(
            {"action": "request_game", "game_id": "romm-42"},
            idempotency_key="device-1-request-42",
            requester="family-room",
        )
        self.assertTrue(created)
        self.assertEqual("pending", proposal["status"])
        self.assertNotIn("download_url", proposal)
        self.assertNotIn("path", proposal)

    def test_install_requires_device(self):
        with self.assertRaisesRegex(ValidationError, "device_id"):
            self.store.create(
                {"action": "install_game", "game_id": "42"},
                idempotency_key="install-42",
                requester="family-room",
            )

    def test_idempotent_replay_returns_same_proposal(self):
        arguments = dict(
            payload={"action": "request_game", "game_id": "42"},
            idempotency_key="request-42",
            requester="family-room",
        )
        first, created = self.store.create(**arguments)
        second, replay_created = self.store.create(**arguments)
        self.assertTrue(created)
        self.assertFalse(replay_created)
        self.assertEqual(first, second)

    def test_idempotency_key_cannot_change_meaning(self):
        self.store.create(
            {"action": "request_game", "game_id": "42"},
            idempotency_key="same-key",
            requester="family-room",
        )
        with self.assertRaisesRegex(ValidationError, "reused"):
            self.store.create(
                {"action": "request_game", "game_id": "43"},
                idempotency_key="same-key",
                requester="family-room",
            )

    def test_unknown_fields_are_rejected(self):
        with self.assertRaisesRegex(ValidationError, "unknown fields"):
            self.store.create(
                {"action": "request_game", "game_id": "42", "url": "secret"},
                idempotency_key="request-42",
                requester="family-room",
            )


class GateTests(unittest.TestCase):
    def test_repository_gate_is_closed(self):
        gate = BROKER_ROOT.parent / "config" / "release-gate.json"
        self.assertFalse(read_gate(str(gate))["open"])

    def test_gate_needs_all_flags_and_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gate.json"
            document = {
                "astertv_v3_deployed": True,
                "astertv_v3_owner_accepted": True,
                "v4_client_work_allowed": True,
                "evidence_refs": [],
            }
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertFalse(read_gate(str(path))["open"])
            document["evidence_refs"] = ["docs/evidence/acceptance.md"]
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertTrue(read_gate(str(path))["open"])


class RomMSanitizationTests(unittest.TestCase):
    def test_only_allowlisted_catalog_fields_leave_broker(self):
        sanitized = RomMClient._sanitize(
            {
                "id": 42,
                "name": "Synthetic Fixture",
                "platform": {"slug": "fixture-console"},
                "url_cover": "/assets/42.png",
                "fs_path": "/private/library/file.rom",
                "download_url": "https://example.invalid/key=secret",
            }
        )
        self.assertEqual(
            {"id", "name", "platform_slug", "cover_url"}, set(sanitized)
        )


if __name__ == "__main__":
    unittest.main()

