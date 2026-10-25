import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops" / "credential-broker"))
from broker_core import BrokerStore

SPEC = importlib.util.spec_from_file_location("m1_check", Path(__file__).with_name("m1_ceremony_db_check.py"))
CHECK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(CHECK)


class M1CeremonyDbCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "broker.db"
        self.now = 10_000
        self.store = BrokerStore(self.path, clock=lambda: self.now)
        self.store.register_agent(CHECK.AGENT, 1904)
        self.store.set_agent_state(CHECK.AGENT, "operator")
        self.store.register_service(CHECK.SERVICE)
        self.store.register_capability(CHECK.CAPABILITY, CHECK.SERVICE, "red")
        self.store.grant_capability(CHECK.AGENT, CHECK.CAPABILITY)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def run_ceremony(self):
        baseline = CHECK.snapshot(self.path)
        CHECK.validate_pre(baseline)
        payload = {"case": "fictional-no-executor", "target": "none"}
        request = self.store.create_request(
            CHECK.AGENT, CHECK.CAPABILITY, payload, ttl_seconds=300,
            display={"reason": "Bounded fictional Red approval test", "target": "No executor"},
        )
        self.now += 5
        actor = "a" * 64
        self.store.approve_request(request.request_id, request.payload_hash, actor=actor,
                                   auth_time=self.now, assurance="passkey")
        self.now += 1
        self.store.consume_request(request.request_id, payload, agent_id=CHECK.AGENT)
        with self.assertRaisesRegex(Exception, "not approved"):
            self.store.consume_request(request.request_id, payload, agent_id=CHECK.AGENT)
        self.store.set_agent_state(CHECK.AGENT, "operator", actor=actor)
        return baseline, request

    def test_exact_ceremony_passes(self):
        baseline, request = self.run_ceremony()
        result = CHECK.validate_post(self.path, baseline, request.request_id, request.payload_hash)
        self.assertEqual("pass", result["decision"])
        self.assertEqual(4, len(result["audit_events"]))

    def test_extra_audit_event_fails(self):
        baseline, request = self.run_ceremony()
        self.store.set_agent_state(CHECK.AGENT, "operator", actor="a" * 64)
        with self.assertRaisesRegex(CHECK.CheckError, "unexpected-table-delta"):
            CHECK.validate_post(self.path, baseline, request.request_id, request.payload_hash)

    def test_wrong_payload_hash_fails(self):
        baseline, request = self.run_ceremony()
        with self.assertRaisesRegex(CHECK.CheckError, "request-payload-hash"):
            CHECK.validate_post(self.path, baseline, request.request_id, "b" * 64)

    def test_precheck_rejects_active_request(self):
        self.store.create_request(CHECK.AGENT, CHECK.CAPABILITY, {})
        with self.assertRaisesRegex(CHECK.CheckError, "active-requests"):
            CHECK.validate_pre(CHECK.snapshot(self.path))

    def test_baseline_file_rejects_wrong_schema(self):
        path = Path(self.temp.name) / "baseline.json"
        path.write_text(json.dumps({"schema": 2}))
        with self.assertRaisesRegex(CHECK.CheckError, "schema"):
            CHECK.load_baseline(path)


if __name__ == "__main__":
    unittest.main()
