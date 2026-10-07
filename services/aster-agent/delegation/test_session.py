import tempfile
import unittest
from pathlib import Path

from session import Session
from store import DispatchStore
from test_contract import answer, end


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = DispatchStore(Path(self.tmp.name) / "jobs.sqlite")
        self.session = Session(self.store, "j", "t")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def start(self):
        self.session.prepare("fictional fixture")
        self.session.acknowledge("u")

    def test_events_before_ack_are_delivered_after_durable_binding(self):
        self.session.prepare("fixture")
        self.session.receive(answer())
        self.session.receive(end())
        self.assertEqual(self.session.answer, "")
        self.session.acknowledge("u")
        self.assertEqual(self.session.answer, "Verified result")
        self.assertEqual(self.store.inspect("j"), ("completed", "t", "u"))

    def test_lost_ack_does_not_allow_retry(self):
        self.session.prepare("fixture"); self.session.disconnect()
        replacement = Session(self.store, "j", "t")
        with self.assertRaises(ValueError):
            replacement.prepare("fixture")
        self.assertEqual(self.session.answer, "")

    def test_store_failure_prevents_dispatch(self):
        self.store.close()
        with self.assertRaises(Exception):
            self.session.prepare("fixture")
        self.assertEqual(self.session.state, "new")

    def test_quota_and_auth_are_classified_without_error_text(self):
        for index, (code, label) in enumerate([
            ("usageLimitExceeded", "subscription_limit"),
            ("unauthorized", "authentication"),
            ("rateLimitExceeded", "rate_limit")]):
            s = Session(self.store, str(index), "t")
            s.prepare("fixture"); s.acknowledge("u")
            m = end("failed")
            m["params"]["turn"]["error"] = {"codexErrorInfo": code, "message": "private"}
            s.receive(m)
            self.assertEqual(s.failure_class, label)
            self.assertEqual(s.answer, "")

    def test_unrelated_completion_does_not_finish_job(self):
        self.start()
        m = end(); m["params"]["turn"]["id"] = "different"
        self.session.receive(m)
        self.assertEqual(self.session.state, "running")
        self.assertEqual(self.store.inspect("j")[0], "running")

    def test_cancel_ack_required(self):
        self.start()
        self.assertEqual(self.session.cancel()["method"], "turn/interrupt")
        self.assertEqual(self.session.state, "cancel_requested")
        self.session.receive(end("interrupted"))
        self.assertEqual(self.store.inspect("j")[0], "interrupted")

    def test_approval_request_blocks_answer(self):
        self.start()
        self.session.receive({"id": 7, "method": "tool/request"})
        self.session.receive(answer()); self.session.receive(end())
        self.assertEqual(self.session.answer, "")
        self.assertEqual(self.session.state, "blocked_server_request")

    def test_duplicate_terminal_is_ignored(self):
        self.start()
        self.session.receive(answer()); self.session.receive(end()); self.session.receive(end())
        self.assertEqual(self.session.answer, "Verified result")

    def test_pre_ack_buffer_drops_reasoning_and_is_bounded(self):
        self.session.prepare("fixture")
        m = answer(); m["params"]["item"]["type"] = "reasoning"
        self.session.receive(m)
        self.assertEqual(self.session.pending, [])
        with self.assertRaises(ValueError):
            self.session.receive(answer("x" * 131073))
        self.assertEqual(self.session.state, "unknown")
        self.assertEqual(self.session.pending, [])
