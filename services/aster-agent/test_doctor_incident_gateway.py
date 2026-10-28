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

    def test_owner_can_request_content_minimized_model_proposal(self):
        claims = lambda value: {"sub": "jason-sub"} if value == "Bearer jwt-jason" else None
        with patch.object(agent, "lab_operations", self.operations), \
             patch.object(agent, "_authentik_claims", side_effect=claims), \
             patch.object(agent, "ASTER_API_KEY", "legacy"), \
             patch.object(agent, "LLAMA_API_KEY", "fixture-llama-key"), \
             patch.object(agent, "SYSADMIN_DOCTOR_EVIDENCE", True), \
             patch.object(agent, "SYSADMIN_INCIDENT_STATE", Path(self.tmp.name) / "incidents.sqlite3"), \
             patch.object(agent, "HEALTH_REPORT_PATH", self.report), \
             patch.object(agent, "_sysadmin_incident_store", None), \
             patch.object(agent, "propose_and_bind_follow_up", return_value={
                 "state_digest": "a" * 64,
                 "decision_count": 1,
                 "consumed_count": 0,
                 "pending": {"decision_ref": "b" * 16, "disposition": "observe",
                             "target": "aster-gateway", "kind": "status"},
             }) as propose:
            with TestClient(agent.app) as client:
                created = client.post(
                    "/v1/sysadmin/incidents/doctor", json={},
                    headers={"Authorization": "Bearer jwt-jason"},
                ).json()
                incident_id = created["incident"]["incident_id"]
                denied = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/propose",
                    headers={"Authorization": "Bearer legacy"},
                )
                self.assertEqual(denied.status_code, 403)
                accepted = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/propose",
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(accepted.status_code, 200, accepted.text)
                self.assertNotIn("hypothesis", accepted.text)
                propose.assert_called_once_with(
                    agent._doctor_incident_store(), incident_id, "fixture-llama-key"
                )

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

    def test_owner_can_run_only_the_pending_registered_gateway_observation(self):
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
                    "/v1/sysadmin/incidents/doctor", json={},
                    headers={"Authorization": "Bearer jwt-jason"},
                ).json()
                incident_id = created["incident"]["incident_id"]
                current = agent._doctor_incident_store().load(
                    incident_id, datetime.now(timezone.utc)
                )
                selected = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/follow-up",
                    json={
                        "schema_version": 1,
                        "state_digest": incident_state_digest(current),
                        "hypothesis_summary": "Gateway availability is the next bounded check.",
                        "disposition": "observe",
                        "target": "aster-gateway",
                        "kind": "status",
                    },
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(200, selected.status_code, selected.text)
                denied = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/observe",
                    headers={"Authorization": "Bearer legacy"},
                )
                self.assertEqual(403, denied.status_code)
                observed = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/observe",
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(200, observed.status_code, observed.text)
                result = observed.json()["incident"]
                self.assertEqual(2, result["observation_count"])
                self.assertEqual("aster-gateway", result["observations"][-1]["target"])
                self.assertEqual("ok", result["observations"][-1]["state"])
                journal = agent._doctor_incident_store().followup_journal_snapshot(
                    incident_id, datetime.now(timezone.utc)
                )
                self.assertEqual(1, journal["consumed_count"])
                self.assertIsNone(journal["pending"])
                repeated = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/observe",
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(409, repeated.status_code)

    def test_three_registered_followups_complete_adaptive_loop_without_hypothesis_egress(self):
        claims = lambda value: {"sub": "jason-sub"} if value == "Bearer jwt-jason" else None
        with patch.object(agent, "lab_operations", self.operations), \
             patch.object(agent, "_authentik_claims", side_effect=claims), \
             patch.object(agent, "SYSADMIN_DOCTOR_EVIDENCE", True), \
             patch.object(agent, "SYSADMIN_INCIDENT_STATE", Path(self.tmp.name) / "incidents.sqlite3"), \
             patch.object(agent, "HEALTH_REPORT_PATH", self.report), \
             patch.object(agent, "_sysadmin_incident_store", None):
            with TestClient(agent.app) as client:
                created = client.post(
                    "/v1/sysadmin/incidents/doctor", json={},
                    headers={"Authorization": "Bearer jwt-jason"},
                ).json()
                incident_id = created["incident"]["incident_id"]

                def select(target, hypothesis, kind="status"):
                    current = agent._doctor_incident_store().load(
                        incident_id, datetime.now(timezone.utc)
                    )
                    response = client.post(
                        f"/v1/sysadmin/incidents/{incident_id}/follow-up",
                        json={
                            "schema_version": 1,
                            "state_digest": incident_state_digest(current),
                            "hypothesis_summary": hypothesis,
                            "disposition": "observe",
                            "target": target,
                            "kind": kind,
                        },
                        headers={"Authorization": "Bearer jwt-jason"},
                    )
                    self.assertEqual(200, response.status_code, response.text)

                select("aster-gateway", "private-gateway-hypothesis-marker")
                first = client.post(
                    f"/v1/sysadmin/incidents/{incident_id}/observe",
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertEqual(200, first.status_code, first.text)

                select("forgejo-main", "private-forgejo-hypothesis-marker", "git")
                forgejo_observed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                forgejo_envelope = {
                    "schema_version": 1,
                    "producer": "forgejo-main-report/v1",
                    "produced_at": forgejo_observed,
                    "observation": {
                        "evidence_id": "forgejo-route-fixture",
                        "incident_id": incident_id,
                        "target": "forgejo-main",
                        "kind": "git",
                        "observed_at": forgejo_observed,
                        "state": "ok",
                        "summary": "The sanitized Forgejo report is healthy.",
                        "facts": {"repository_count": 1},
                        "truncated": False,
                    },
                }
                with patch(
                    "sysadmin_registered_producer._forgejo_status_envelope",
                    return_value=forgejo_envelope,
                ):
                    forgejo = client.post(
                        f"/v1/sysadmin/incidents/{incident_id}/observe",
                        headers={"Authorization": "Bearer jwt-jason"},
                    )
                self.assertEqual(200, forgejo.status_code, forgejo.text)

                select("inference-server", "private-inference-hypothesis-marker")
                observed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                inference_envelope = {
                    "schema_version": 1,
                    "producer": "inference-server-health/v1",
                    "produced_at": observed,
                    "observation": {
                        "evidence_id": "inference-health-route-fixture",
                        "incident_id": incident_id,
                        "target": "inference-server",
                        "kind": "status",
                        "observed_at": observed,
                        "state": "ok",
                        "summary": "The registered inference health endpoint reported ok.",
                        "facts": {"service": "aster-llama", "endpoint": "health"},
                        "truncated": False,
                    },
                }
                with patch(
                    "sysadmin_registered_producer._inference_status_envelope",
                    return_value=inference_envelope,
                ):
                    second = client.post(
                        f"/v1/sysadmin/incidents/{incident_id}/observe",
                        headers={"Authorization": "Bearer jwt-jason"},
                    )
                self.assertEqual(200, second.status_code, second.text)
                incident = second.json()["incident"]
                self.assertEqual(4, incident["observation_count"])
                self.assertEqual("inference-server", incident["observations"][-1]["target"])
                self.assertEqual("bounded", incident["next"]["state"])
                journal = agent._doctor_incident_store().followup_journal_snapshot(
                    incident_id, datetime.now(timezone.utc)
                )
                self.assertEqual(3, journal["decision_count"])
                self.assertEqual(3, journal["consumed_count"])
                self.assertIsNone(journal["pending"])
                stream = client.get(
                    f"/v1/sysadmin/incidents/{incident_id}/stream",
                    headers={"Authorization": "Bearer jwt-jason"},
                )
                self.assertNotIn("private-gateway-hypothesis-marker", stream.text)
                self.assertNotIn("private-inference-hypothesis-marker", stream.text)
                self.assertNotIn("private-forgejo-hypothesis-marker", stream.text)

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
