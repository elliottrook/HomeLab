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
from sysadmin_followup_selector import incident_state_digest


NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc)


class DoctorIncidentGatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.report = Path(self.tmp.name) / "latest.json"
        self.report.write_text(json.dumps({
            "schema": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "warning",
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
                denied = client.post("/v1/sysadmin/incidents/doctor", json={}, headers={"Authorization": "Bearer legacy"})
                self.assertEqual(denied.status_code, 403)
                created = client.post("/v1/sysadmin/incidents/doctor", json={}, headers={"Authorization": "Bearer jwt-jason"})
                self.assertEqual(created.status_code, 200, created.text)
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

    def test_owner_can_journal_no_effect_followup_and_legacy_key_cannot(self):
        claims = lambda value: {"sub": "jason-sub"} if value == "Bearer jwt-jason" else None
        with patch.object(agent, "lab_operations", self.operations), \
             patch.object(agent, "_authentik_claims", side_effect=claims), \
             patch.object(agent, "ASTER_API_KEY", "legacy"), \
             patch.object(agent, "SYSADMIN_DOCTOR_EVIDENCE", True), \
             patch.object(agent, "SYSADMIN_INCIDENT_STATE", Path(self.tmp.name) / "incidents.sqlite3"), \
             patch.object(agent, "HEALTH_REPORT_PATH", self.report), \
             patch.object(agent, "_sysadmin_incident_store", None):
            with TestClient(agent.app) as client:
                created = client.post(
                    "/v1/sysadmin/incidents/doctor",
                    json={},
                    headers={"Authorization": "Bearer jwt-jason"},
                ).json()
                incident_id = created["incident"]["incident_id"]
                store = agent._doctor_incident_store()
                current = store.load(incident_id, datetime.now(timezone.utc))
                body = {
                    "schema_version": 1,
                    "state_digest": incident_state_digest(current),
                    "hypothesis_summary": "private-terminal-hypothesis",
                    "disposition": "escalate",
                    "target": None,
                    "kind": None,
                }
                denied = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/follow-up",
                    json=body,
                    headers={"Authorization": "Bearer legacy"},
                )
                self.assertEqual(denied.status_code, 403)
                accepted = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/follow-up",
                    json=body,
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(accepted.status_code, 200, accepted.text)
                result = accepted.json()
                self.assertEqual(result["decision_count"], 1)
                self.assertEqual(result["pending"]["disposition"], "escalate")
                self.assertNotIn("private-terminal-hypothesis", accepted.text)
                stream = client.get(
                    f"/v1/sysadmin/incidents/{incident_id}/stream",
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertNotIn("private-terminal-hypothesis", stream.text)
                self.assertIn('"disposition":"escalate"', stream.text)

    def test_followup_rejects_stale_state_without_new_journal_row(self):
        claims = lambda value: {"sub": "jason-sub"} if value == "Bearer jwt-jason" else None
        with patch.object(agent, "lab_operations", self.operations), \
             patch.object(agent, "_authentik_claims", side_effect=claims), \
             patch.object(agent, "SYSADMIN_DOCTOR_EVIDENCE", True), \
             patch.object(agent, "SYSADMIN_INCIDENT_STATE", Path(self.tmp.name) / "incidents.sqlite3"), \
             patch.object(agent, "HEALTH_REPORT_PATH", self.report), \
             patch.object(agent, "_sysadmin_incident_store", None):
            with TestClient(agent.app) as client:
                created = client.post(
                    "/v1/sysadmin/incidents/doctor",
                    json={},
                    headers={"Authorization": "Bearer jwt-jason"},
                ).json()
                incident_id = created["incident"]["incident_id"]
                rejected = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/follow-up",
                    json={
                        "schema_version": 1,
                        "state_digest": "0" * 64,
                        "hypothesis_summary": "A stale proposal.",
                        "disposition": "escalate",
                        "target": None,
                        "kind": None,
                    },
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(rejected.status_code, 409)
                summary = agent._doctor_incident_store().followup_journal_snapshot(
                    incident_id, datetime.now(timezone.utc)
                )
                self.assertEqual(summary["decision_count"], 0)

    def test_followup_rejects_boolean_schema_version(self):
        claims = lambda value: {"sub": "jason-sub"} if value == "Bearer jwt-jason" else None
        with patch.object(agent, "lab_operations", self.operations), \
             patch.object(agent, "_authentik_claims", side_effect=claims), \
             patch.object(agent, "SYSADMIN_DOCTOR_EVIDENCE", True), \
             patch.object(agent, "SYSADMIN_INCIDENT_STATE", Path(self.tmp.name) / "incidents.sqlite3"), \
             patch.object(agent, "HEALTH_REPORT_PATH", self.report), \
             patch.object(agent, "_sysadmin_incident_store", None):
            with TestClient(agent.app) as client:
                created = client.post(
                    "/v1/sysadmin/incidents/doctor",
                    json={},
                    headers={"Authorization": "Bearer jwt-jason"},
                ).json()
                incident_id = created["incident"]["incident_id"]
                current = agent._doctor_incident_store().load(
                    incident_id, datetime.now(timezone.utc)
                )
                rejected = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/follow-up",
                    json={
                        "schema_version": True,
                        "state_digest": incident_state_digest(current),
                        "hypothesis_summary": "A malformed-version proposal.",
                        "disposition": "escalate",
                        "target": None,
                        "kind": None,
                    },
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(rejected.status_code, 422)


if __name__ == "__main__":
    unittest.main()
