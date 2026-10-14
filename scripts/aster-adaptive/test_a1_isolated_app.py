"""Fixture-only sidecar assembly; no Aster import, socket or model call."""
import asyncio
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from a1_isolated_app import create_app
from aster_full_path_request import wire_bytes_for
from test_aster_full_path_request import fixture

INGRESS = b"fictional-ingress-key"
INNER = "fictional-isolated-inner-key"


class IsolatedAppTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.root.chmod(0o700)
        self.journal = self.root / "journal"
        self.clock = self.root / "clock"
        self.knowledge = self.root / "knowledge"
        for path in (self.journal, self.clock, self.knowledge):
            path.mkdir(mode=0o700)
        body = wire_bytes_for(fixture())
        self.body = body
        digests = [hashlib.sha256(body).hexdigest()]
        digests.extend(f"{index:064x}" for index in range(1, 20))
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps({
            "schema_version": "aster-a1-isolated-config.v0",
            "ingress_token_sha256": hashlib.sha256(INGRESS).hexdigest(),
            "request_sha256s": digests,
            "attempt_journal_dir": str(self.journal),
            "clock_dir": str(self.clock),
        }))
        self.config.chmod(0o600)
        self.env = {
            "ASTER_A1_TEST_MODE": "isolated-20case",
            "ASTER_MAX_RESPONSE_TOKENS": "256",
            "ASTER_MAX_TOOL_ROUNDS": "0",
            "ASTER_REQUEST_TIMEOUT": "60",
            "ASTER_LLAMA_MODEL": "qwen3.5-9b",
            "ASTER_LLAMA_BASE_URL": "http://192.168.70.12:11435/v1",
            "ASTER_API_KEY": INNER,
            "ASTER_LLAMA_API_KEY": "fictional-isolated-backend-key",
            "ASTER_BROKER_APPROVAL_SOCKET": "/run/aster-a1-test/absent-approval.sock",
            "ASTER_OPENBAO_URL": "http://127.0.0.1:1",
            "ASTER_NOTIFICATION_KEY": "/run/aster-a1-test/absent-vapid.pem",
            "ASTER_KNOWLEDGE_DIR": str(self.knowledge),
        }

    def build(self, *, env=None, loader=None):
        return create_app(config_path=self.config, env=env or self.env,
                          uid=os.getuid(), app_loader=loader or (lambda: self.fake_app))

    async def fake_app(self, scope, receive, send):
        self.assertEqual([value for key, value in scope["headers"]
                          if key == b"authorization"], [b"Bearer " + INNER.encode()])
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}", "more_body": False})

    def test_assembly_forwards_one_frozen_request_and_writes_content_free_clock(self):
        app = self.build()
        events = []

        async def receive():
            return {"type": "http.request", "body": self.body, "more_body": False}

        async def send(event):
            events.append(event)

        asyncio.run(app({"type": "http", "path": "/v1/chat/completions",
                         "method": "POST", "headers": [
                             (b"content-type", b"application/json"),
                             (b"authorization", b"Bearer " + INGRESS)]}, receive, send))
        self.assertEqual(events[0]["status"], 200)
        rows = (self.clock / "asgi-clock.jsonl").read_text().splitlines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0])["schema_version"], "aster-asgi-clock.v0")
        self.assertNotIn("fictional", rows[0])
        self.assertEqual(len(list(self.journal.iterdir())), 1)

    def test_privileged_or_unpinned_environment_fails_before_loader(self):
        for key, value in (("ASTER_MAX_RESPONSE_TOKENS", "160"),
                           ("ASTER_MAX_TOOL_ROUNDS", "4"),
                           ("ASTER_LAB_TARGETS", "doctor"),
                           ("ASTER_BROKER_APPROVAL_SOCKET", "/run/homelab-broker/approval.sock"),
                           ("ASTER_LLAMA_BASE_URL", "https://cloud.example/v1"),
                           ("ASTER_API_KEY", "short")):
            with self.subTest(key=key):
                env = dict(self.env)
                env[key] = value
                called = []
                with self.assertRaises(ValueError):
                    self.build(env=env, loader=lambda: called.append(True))
                self.assertEqual(called, [])

    def test_sidecar_requires_nonroot_and_new_clock_file(self):
        with self.assertRaises(ValueError):
            create_app(config_path=self.config, env=self.env, uid=0,
                       app_loader=lambda: self.fake_app)
        self.build()
        with self.assertRaises(FileExistsError):
            self.build()

    def test_config_parent_must_be_owner_only(self):
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):
            self.build()


if __name__ == "__main__":
    unittest.main()
