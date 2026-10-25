import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fixed_doctor_capability import CAPABILITY, METHOD, FixedDoctorDenied, execute_fixed_doctor_read


NOW = datetime(2026, 10, 25, 23, 0, tzinfo=timezone.utc)
PRIVATE = "192.168.70.10 token=FIXTURE_NOT_A_SECRET restart-this-service"


class FixedDoctorCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.aggregate = root / "aggregate.json"
        self.structured = root / "structured.json"

    def write_pair(self, *, state="fail", check_id="aster.agent_inference",
                   when=NOW - timedelta(minutes=2), extra=None):
        generated = when.isoformat().replace("+00:00", "Z")
        aggregate = {
            "schema": 1, "generated_at": generated, "status": "failed",
            "checks": [{"name": PRIVATE, "status": "fail", "summary": PRIVATE}],
        }
        raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.aggregate.write_bytes(raw)
        structured = {
            "schema": 2, "generated_at": generated, "run_id": "a" * 32,
            "source_report_digest": hashlib.sha256(raw).hexdigest(),
            "checks": [{"check_id": check_id, "state": state}],
        }
        if extra:
            structured.update(extra)
        self.structured.write_text(json.dumps(structured))
        self.aggregate.chmod(0o600)
        self.structured.chmod(0o600)

    def execute(self, request=None):
        return execute_fixed_doctor_read(
            {"method": METHOD, "arguments": {}} if request is None else request,
            incident_id="incident-fixed-1", aggregate_path=self.aggregate,
            structured_path=self.structured, now=NOW, required_uid=os.getuid(),
        )

    def test_fixed_failure_names_only_registered_check(self):
        self.write_pair()
        result = self.execute()
        self.assertEqual(CAPABILITY, result["capability"])
        self.assertEqual("fail", result["observation"]["state"])
        self.assertEqual({"check_id": "aster.agent_inference"}, result["observation"]["facts"])
        encoded = json.dumps(result)
        self.assertNotIn(PRIVATE, encoded)
        self.assertNotIn("report_digest", encoded)

    def test_fixed_pass_warn_and_unavailable_are_typed(self):
        for state, expected in (("pass", "ok"), ("warn", "warn"), ("unavailable", "unavailable")):
            with self.subTest(state=state):
                self.write_pair(state=state)
                result = self.execute()["observation"]
                self.assertEqual(expected, result["state"])
                self.assertEqual({} if state == "unavailable" else {"check_id": "aster.agent_inference"}, result["facts"])

    def test_request_contract_is_exact(self):
        self.write_pair()
        invalid = (
            {},
            {"method": METHOD, "arguments": {"target": "other"}},
            {"method": "doctor.run", "arguments": {}},
            {"method": METHOD, "arguments": {}, "extra": True},
        )
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(FixedDoctorDenied):
                self.execute(request)

    def test_unknown_stale_and_malformed_evidence_abstains(self):
        self.write_pair(check_id="other.check")
        self.assertEqual("unavailable", self.execute()["observation"]["state"])
        self.write_pair(when=NOW - timedelta(hours=37))
        self.assertEqual("unavailable", self.execute()["observation"]["state"])
        self.write_pair(extra={"private": PRIVATE})
        self.assertEqual("unavailable", self.execute()["observation"]["state"])

    def test_unsafe_file_boundaries_abstain(self):
        self.write_pair()
        self.structured.chmod(0o666)
        self.assertEqual("unavailable", self.execute()["observation"]["state"])
        self.write_pair()
        link = self.structured.with_name("linked.json")
        link.symlink_to(self.structured)
        self.structured = link
        self.assertEqual("unavailable", self.execute()["observation"]["state"])


if __name__ == "__main__":
    unittest.main()
