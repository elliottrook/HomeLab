import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from doctor_incident_adapter import read_doctor_observation
from doctor_model_projection import project_doctor_for_model
from sysadmin_investigation import InvestigationError, Observation


NOW = datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc)
PRIVATE = "fixture-private-marker"


def aggregate(**changes):
    data = dict(
        evidence_id="doctor-" + "a" * 24, incident_id="inc-1",
        target="homelab-doctor", kind="status",
        observed_at=(NOW - timedelta(minutes=2)).isoformat().replace("+00:00", "Z"),
        source="homelab-doctor-report/v1", state="warn",
        summary=PRIVATE, facts={"check_count": 3, "report_digest": "b" * 24},
    )
    data.update(changes)
    return Observation(**data)


class DoctorModelProjectionTests(unittest.TestCase):
    def test_aggregate_excludes_private_summary_and_digest(self):
        result = project_doctor_for_model(aggregate(), NOW)
        self.assertEqual(result["facts"], {"check_count": 3})
        self.assertEqual(result["state"], "warn")
        self.assertNotIn(PRIVATE, json.dumps(result))
        self.assertNotIn("b" * 24, json.dumps(result))

    def test_real_aggregate_adapter_output_passes_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps({
                "schema": 1,
                "generated_at": (NOW - timedelta(minutes=2)).isoformat().replace("+00:00", "Z"),
                "status": "warning",
                "checks": [{"name": "Doctor", "status": "warn", "summary": PRIVATE}],
            }))
            result = project_doctor_for_model(read_doctor_observation("inc-1", path, NOW), NOW)
        self.assertEqual(result["facts"], {"check_count": 1})
        self.assertNotIn(PRIVATE, json.dumps(result))

    def test_structured_check_projects_fixed_id_only(self):
        record = aggregate(source="homelab-doctor-structured/v2", state="fail",
                           facts={"check_id": "aster.agent_inference", "report_digest": "c" * 24})
        result = project_doctor_for_model(record, NOW)
        self.assertEqual(result["facts"], {"check_id": "aster.agent_inference"})
        self.assertNotIn(PRIVATE, json.dumps(result))

    def test_unavailable_remains_unavailable(self):
        result = project_doctor_for_model(aggregate(state="unavailable", facts={"reason": "stale"}), NOW)
        self.assertEqual(result["state"], "unavailable")
        self.assertEqual(result["facts"], {"unavailable_reason": "stale"})
        result = project_doctor_for_model(aggregate(source="homelab-doctor-structured/v2",
                                                   state="unavailable", facts={}), NOW)
        self.assertEqual(result["facts"], {})

    def test_unregistered_or_extra_producer_data_fails_closed(self):
        for record in (
            aggregate(target="aster-gateway"),
            aggregate(source="other-producer/v1"),
            aggregate(facts={"check_count": 3, "report_digest": "b" * 24, "debug": PRIVATE}),
            aggregate(facts={"check_count": True, "report_digest": "b" * 24}),
            aggregate(source="homelab-doctor-structured/v2", facts={"check_id": PRIVATE, "report_digest": "c" * 24}),
            aggregate(state="unavailable", facts={"reason": PRIVATE}),
            aggregate(truncated=True),
            aggregate(observed_at=(NOW - timedelta(hours=37)).isoformat()),
        ):
            with self.subTest(record=record), self.assertRaises(InvestigationError):
                project_doctor_for_model(record, NOW)


if __name__ == "__main__":
    unittest.main()
