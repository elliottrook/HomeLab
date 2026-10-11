import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from doctor_incident_adapter import read_doctor_observation
from doctor_structured_incident_adapter import read_doctor_structured_observation


NOW = datetime(2026, 10, 10, 20, 0, tzinfo=timezone.utc)
PRIVATE_MARKER = "token=FIXTURE_NOT_A_SECRET"


class StructuredDoctorAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.aggregate_path = self.directory / "aggregate.json"
        self.structured_path = self.directory / "structured.json"

    def write_pair(self, *, state="fail", timestamp=None, check_id="aster.agent_inference", duplicate=False):
        generated_at = timestamp or (NOW - timedelta(minutes=2)).isoformat().replace("+00:00", "Z")
        aggregate = {
            "schema": 1, "generated_at": generated_at, "status": "failed",
            "checks": [{"name": "HomeLab Doctor", "status": "fail", "summary": PRIVATE_MARKER}],
        }
        aggregate_raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.aggregate_path.write_bytes(aggregate_raw)
        self.aggregate_path.chmod(0o600)
        check = {"check_id": check_id, "state": state}
        structured = {
            "schema": 2, "generated_at": generated_at, "run_id": "a" * 32,
            "source_report_digest": hashlib.sha256(aggregate_raw).hexdigest(),
            "checks": [check, check] if duplicate else [check],
        }
        self.structured_path.write_text(json.dumps(structured), encoding="utf-8")
        self.structured_path.chmod(0o600)
        return structured

    def read(self, *, required_uid=None):
        return read_doctor_structured_observation(
            "incident-1", self.aggregate_path, self.structured_path, NOW,
            required_uid=os.getuid() if required_uid is None else required_uid,
        ).validate(NOW)

    def test_one_failure_identifies_subsystem_without_summary(self):
        self.write_pair()
        baseline = read_doctor_observation("incident-1", self.aggregate_path, NOW).validate(NOW)
        candidate = self.read()
        self.assertNotIn("check_id", baseline["facts"])
        self.assertEqual(candidate["state"], "fail")
        self.assertEqual(candidate["facts"]["check_id"], "aster.agent_inference")
        self.assertNotIn(PRIVATE_MARKER, json.dumps(candidate))
        self.assertEqual(candidate["age_seconds"], 120)

    def test_typed_pass_warn_and_unavailable(self):
        for state, expected in (("pass", "ok"), ("warn", "warn"), ("unavailable", "unavailable")):
            with self.subTest(state=state):
                self.write_pair(state=state)
                record = self.read()
                self.assertEqual(record["state"], expected)
                if state == "unavailable":
                    self.assertNotIn("check_id", record["facts"])

    def test_stale_future_digest_and_time_mismatch_abstain(self):
        for timestamp in (
            (NOW - timedelta(hours=37)).isoformat(),
            (NOW + timedelta(minutes=1)).isoformat(),
        ):
            with self.subTest(timestamp=timestamp):
                self.write_pair(timestamp=timestamp)
                self.assertEqual(self.read()["state"], "unavailable")
        structured = self.write_pair()
        structured["source_report_digest"] = "0" * 64
        self.structured_path.write_text(json.dumps(structured))
        self.assertEqual(self.read()["state"], "unavailable")
        structured = self.write_pair()
        structured["generated_at"] = NOW.isoformat()
        self.structured_path.write_text(json.dumps(structured))
        self.assertEqual(self.read()["state"], "unavailable")

    def test_unknown_duplicate_extra_field_and_unsafe_files_abstain(self):
        self.write_pair(check_id="unknown.check")
        self.assertEqual(self.read()["state"], "unavailable")
        self.write_pair(duplicate=True)
        self.assertEqual(self.read()["state"], "unavailable")
        structured = self.write_pair()
        structured["raw_summary"] = PRIVATE_MARKER
        self.structured_path.write_text(json.dumps(structured))
        self.assertEqual(self.read()["state"], "unavailable")
        self.write_pair()
        raw = self.structured_path.read_text()
        self.structured_path.write_text(raw.replace('"schema": 2', '"schema": 2, "schema": 2'))
        self.assertEqual(self.read()["state"], "unavailable")
        self.write_pair()
        self.structured_path.chmod(0o666)
        self.assertEqual(self.read()["state"], "unavailable")
        self.write_pair()
        self.aggregate_path.chmod(0o644)
        self.assertEqual(self.read()["state"], "unavailable")
        self.write_pair()
        self.assertEqual(self.read(required_uid=os.getuid() + 1)["state"], "unavailable")
        target = self.structured_path
        link = self.directory / "linked.json"
        link.symlink_to(target)
        self.structured_path = link
        self.assertEqual(self.read()["state"], "unavailable")

    def test_malformed_aggregate_rejected_even_when_digest_matches(self):
        for field, replacement in (
            ("status", "unknown"),
            ("checks", "not-a-list"),
            ("checks", [{"name": "Doctor", "status": "unknown", "summary": PRIVATE_MARKER}]),
            ("checks", [{"name": "Doctor", "status": "fail", "summary": [PRIVATE_MARKER]}]),
        ):
            with self.subTest(field=field, replacement=replacement):
                structured = self.write_pair()
                aggregate = json.loads(self.aggregate_path.read_text())
                aggregate[field] = replacement
                raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
                self.aggregate_path.write_bytes(raw)
                structured["source_report_digest"] = hashlib.sha256(raw).hexdigest()
                self.structured_path.write_text(json.dumps(structured))
                self.assertEqual(self.read()["state"], "unavailable")


if __name__ == "__main__":
    unittest.main()
