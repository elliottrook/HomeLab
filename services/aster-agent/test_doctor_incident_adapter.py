import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from doctor_incident_adapter import read_doctor_observation
from sysadmin_investigation import InvestigationError


NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc)


class DoctorAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "latest.json"

    def write(self, **changes):
        report = {
            "schema": 1, "generated_at": "2026-09-28T17:58:00Z", "status": "warning",
            "checks": [{"name": "Doctor", "status": "warn", "summary": "Fixture warning."}],
        }
        report.update(changes)
        self.path.write_text(json.dumps(report))

    def test_reads_only_the_fixed_sanitized_schema(self):
        self.write()
        observation = read_doctor_observation("inc-1", self.path, NOW)
        record = observation.validate(NOW)
        self.assertEqual(record["target"], "homelab-doctor")
        self.assertEqual(record["state"], "warn")
        self.assertEqual(record["facts"]["check_count"], 1)
        self.assertEqual(record["age_seconds"], 120)

    def test_malformed_future_stale_and_unknown_fields_fail_closed(self):
        for report in (
            {"schema": 1, "generated_at": "2026-09-28T18:01:00Z", "status": "healthy", "checks": []},
            {"schema": 1, "generated_at": (NOW - timedelta(hours=37)).isoformat(), "status": "healthy", "checks": []},
            {"schema": 1, "generated_at": "2026-09-28T17:58:00Z", "status": "healthy", "checks": [], "extra": True},
        ):
            self.path.write_text(json.dumps(report))
            record = read_doctor_observation("inc-1", self.path, NOW).validate(NOW)
            self.assertEqual(record["state"], "unavailable")

    def test_never_accepts_raw_or_oversized_input(self):
        self.path.write_text("not-json")
        self.assertEqual(read_doctor_observation("inc-1", self.path, NOW).validate(NOW)["state"], "unavailable")
        self.path.write_bytes(b"x" * 65_537)
        self.assertEqual(read_doctor_observation("inc-1", self.path, NOW).validate(NOW)["state"], "unavailable")


if __name__ == "__main__":
    unittest.main()
