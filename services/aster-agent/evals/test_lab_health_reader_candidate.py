"""Dependency-free checks for the local Aster health-reader candidate."""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from compare_doctor_projections import AGENT_DIR, compile_health_function


NOW = datetime(2026, 10, 10, 20, 0, tzinfo=timezone.utc)


class LabHealthReaderCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "latest.json"
        self.read, _ = compile_health_function((AGENT_DIR / "aster_agent.py").read_text(encoding="utf-8"))

    def write_report(self, observed=NOW - timedelta(minutes=2)):
        self.path.write_text(json.dumps({
            "schema": 1,
            "generated_at": observed.isoformat(),
            "status": "warning",
            "checks": [{"name": "HomeLab Doctor", "status": "warn", "summary": "Fixture backup is overdue"}],
        }), encoding="utf-8")
        self.path.chmod(0o600)

    def test_fresh_bounded_summary_still_works(self):
        self.write_report()
        self.path.chmod(0o640)  # Existing published report is root/group-readable.
        result = self.read(self.path, now=NOW)
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["checks"][0]["summary"], "Fixture backup is overdue")

    def test_stale_future_and_invalid_clock_abstain(self):
        for observed in (NOW - timedelta(hours=37), NOW + timedelta(minutes=1)):
            with self.subTest(observed=observed):
                self.write_report(observed)
                self.assertEqual(self.read(self.path, now=NOW)["status"], "unavailable")
        self.write_report()
        self.assertEqual(self.read(self.path, now=NOW.replace(tzinfo=None))["status"], "unavailable")

    def test_symlink_and_writable_report_abstain_without_path_in_error(self):
        self.write_report()
        linked = self.path.with_name("linked.json")
        linked.symlink_to(self.path)
        result = self.read(linked, now=NOW)
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn(str(linked), result["error"])
        self.path.chmod(0o666)
        self.assertEqual(self.read(self.path, now=NOW)["status"], "unavailable")

    def test_invalid_schema_and_oversized_report_abstain(self):
        self.write_report()
        value = json.loads(self.path.read_text())
        del value["schema"]
        self.path.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.read(self.path, now=NOW)["status"], "unavailable")
        self.path.write_bytes(b"x" * 65_537)
        self.assertEqual(self.read(self.path, now=NOW)["status"], "unavailable")

    def test_unhashable_status_values_fail_closed(self):
        self.write_report()
        value = json.loads(self.path.read_text())
        value["status"] = []
        self.path.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.read(self.path, now=NOW)["status"], "unavailable")

        value["status"] = "warning"
        value["checks"][0]["status"] = {}
        self.path.write_text(json.dumps(value), encoding="utf-8")
        result = self.read(self.path, now=NOW)
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["checks"], [])


if __name__ == "__main__":
    unittest.main()
