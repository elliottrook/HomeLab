"""Offline fixtures for Doctor's opt-in, source-owned check evidence."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILDER = ROOT / "build-aster-health-report.py"
DOCTOR = ROOT / "doctor.sh"
sys.path.insert(0, str(ROOT.parent / "services" / "aster-agent"))
from doctor_structured_incident_adapter import read_doctor_structured_observation

HELPER_CODE = (
    "doctor_emit_aster_state() {"
    + DOCTOR.read_text(encoding="utf-8").split("doctor_emit_aster_state() {", 1)[1].split("\n}", 1)[0]
    + "\n}\n"
)


class StructuredDoctorReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.aggregate = self.directory / "aggregate.json"
        self.structured = self.directory / "structured.json"

    def run_fixture(self, body: str):
        doctor = self.directory / "fixture-doctor.sh"
        doctor.write_text("#!/bin/bash\n" + body, encoding="utf-8")
        doctor.chmod(0o700)
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--doctor", str(doctor),
             "--output", str(self.aggregate), "--structured-output", str(self.structured)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(self.aggregate.read_text()), json.loads(self.structured.read_text())

    def test_producer_owned_failure_and_private_summary_exclusion(self):
        body = (
            HELPER_CODE +
            "printf '🔴 Aster service unhealthy: token=FIXTURE_NOT_A_SECRET\\n'\n"
            "doctor_emit_aster_state fail\n"
        )
        aggregate, structured = self.run_fixture(body)
        self.assertEqual(aggregate["schema"], 1)
        self.assertEqual(aggregate["status"], "failed")
        self.assertEqual(structured["schema"], 2)
        self.assertEqual(structured["checks"], [{"check_id": "aster.agent_inference", "state": "fail"}])
        self.assertEqual(structured["generated_at"], aggregate["generated_at"])
        self.assertEqual(structured["source_report_digest"], hashlib.sha256(self.aggregate.read_bytes()).hexdigest())
        self.assertNotIn("FIXTURE_NOT_A_SECRET", self.structured.read_text())
        self.assertEqual(self.structured.stat().st_mode & 0o777, 0o600)
        observed = read_doctor_structured_observation(
            "fixture-incident", self.aggregate, self.structured,
            datetime.now(timezone.utc), required_uid=self.aggregate.stat().st_uid,
        ).validate(datetime.now(timezone.utc))
        self.assertEqual(observed["state"], "fail")
        self.assertEqual(observed["facts"]["check_id"], "aster.agent_inference")
        self.assertNotIn("FIXTURE_NOT_A_SECRET", json.dumps(observed))

    def test_missing_duplicate_or_wrong_run_event_abstains(self):
        helper = HELPER_CODE
        for event in (
            "",
            "doctor_emit_aster_state pass\ndoctor_emit_aster_state fail\n",
            "printf '{\"run_id\":\"00000000000000000000000000000000\",\"check_id\":\"aster.agent_inference\",\"state\":\"fail\"}\\n' >&\"$DOCTOR_STRUCTURED_FD\"\n",
            "printf '{\"run_id\":\"%s\",\"check_id\":\"unknown.check\",\"state\":\"fail\"}\\n' \"$DOCTOR_RUN_ID\" >&\"$DOCTOR_STRUCTURED_FD\"\n",
            "printf '{\"run_id\":\"%s\",\"check_id\":\"aster.agent_inference\",\"state\":\"fail\",\"state\":\"pass\"}\\n' \"$DOCTOR_RUN_ID\" >&\"$DOCTOR_STRUCTURED_FD\"\n",
        ):
            with self.subTest(event=event[:28]):
                _, structured = self.run_fixture(helper + "printf '🟢 Fixture healthy\\n'\n" + event)
                self.assertEqual(structured["checks"][0]["state"], "unavailable")

    def test_unavailable_collection_and_legacy_captured_input(self):
        helper = HELPER_CODE
        _, structured = self.run_fixture(helper + "printf '🟡 Unable to check Aster services\\n'\ndoctor_emit_aster_state unavailable\n")
        self.assertEqual(structured["checks"][0]["state"], "unavailable")
        captured = self.directory / "captured.txt"
        captured.write_text("🟢 Fixture healthy\n", encoding="utf-8")
        legacy = self.directory / "legacy.json"
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--input", str(captured), "--output", str(legacy)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(legacy.read_text())["schema"], 1)

    def test_cannot_publish_structured_candidate(self):
        doctor = self.directory / "unused.sh"
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--doctor", str(doctor),
             "--output", str(self.aggregate), "--structured-output", str(self.structured), "--publish"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.aggregate.exists())
        self.assertFalse(self.structured.exists())

    def test_structured_output_replaces_symlink_without_writing_its_target(self):
        victim = self.directory / "unrelated.txt"
        victim.write_text("untouched", encoding="utf-8")
        self.structured.symlink_to(victim)
        _, structured = self.run_fixture(HELPER_CODE + "printf '🟢 Fixture healthy\\n'\ndoctor_emit_aster_state pass\n")
        self.assertEqual(victim.read_text(), "untouched")
        self.assertFalse(self.structured.is_symlink())
        self.assertEqual(structured["checks"][0]["state"], "pass")


if __name__ == "__main__":
    unittest.main()
