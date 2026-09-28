import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import aster_agent as agent
from lab_operations import LabOperations


NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc)


class DoctorIncidentGatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.report = Path(self.tmp.name) / "latest.json"
        self.report.write_text(json.dumps({
            "schema": 1, "generated_at": "2026-09-28T17:58:00Z", "status": "warning",
            "checks": [{"name": "Doctor", "status": "warn", "summary": "Fixture warning."}],
        }))
        self.operations = LabOperations()
        self.operations.owner = hashlib.sha256((agent.AUTHENTIK_ISSUER + "\0jason-sub").encode()).hexdigest()

    def test_legacy_key_cannot_open_incident_and_owner_can_reconnect(self):
        claims = lambda value: {"sub": "jason-sub"} if value == "Bearer jwt-jason" else None
        with patch.object(agent, "lab_operations", self.operations), \
             patch.object(agent, "_authentik_claims", side_effect=claims), \
             patch.object(agent, "ASTER_API_KEY", "legacy"), \
             patch.object(agent, "SYSADMIN_DOCTOR_EVIDENCE", True), \
             patch.object(agent, "SYSADMIN_INCIDENT_STATE", Path(self.tmp.name) / "incidents.sqlite3"), \
             patch.object(agent, "HEALTH_REPORT_PATH", self.report), \
             patch.object(agent, "_sysadmin_incident_store", None):
            with TestClient(agent.app) as client:
                denied = client.post("/v1/sysadmin/incidents/doctor", headers={"Authorization": "Bearer legacy"})
                self.assertEqual(denied.status_code, 403)
                created = client.post("/v1/sysadmin/incidents/doctor", headers={"Authorization": "Bearer jwt-jason"})
                self.assertEqual(created.status_code, 200)
                snapshot = created.json()
                self.assertEqual(snapshot["incident"]["observations"][0]["state"], "warn")
                incident_id = snapshot["incident"]["incident_id"]
                stream = client.get(f"/v1/sysadmin/incidents/{incident_id}/stream", headers={"Authorization": "Bearer jwt-jason"})
                self.assertEqual(stream.status_code, 200)
                self.assertIn("event: aster.incident", stream.text)
                self.assertNotIn("report_digest", stream.text)

    def test_disabled_pilot_is_not_available(self):
        with patch.object(agent, "SYSADMIN_DOCTOR_EVIDENCE", False):
            with self.assertRaises(Exception) as error:
                agent.start_doctor_incident("test", NOW)
        self.assertIn("disabled", str(error.exception))


if __name__ == "__main__":
    unittest.main()
