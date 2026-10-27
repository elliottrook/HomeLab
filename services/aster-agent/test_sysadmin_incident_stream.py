import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_incident_store import IncidentStore
from sysadmin_followup_selector import incident_state_digest
from sysadmin_incident_stream import incident_presentation, reconnect_frames
from sysadmin_investigation import EvidenceRequest, InvestigationError, create_incident


NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc)
FIXTURE = Path(__file__).with_name("evals") / "sysadmin-producer-fixture.json"


class StreamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = IncidentStore(Path(self.tmp.name) / "incidents.sqlite3")
        incident = create_incident("fixture-incident-001", "Fixture incident", [
            EvidenceRequest("aster-gateway", "status", "Establish gateway state."),
            EvidenceRequest("inference-server", "status", "Check dependency state."),
        ])
        incident.add_hypothesis("This internal hypothesis must not reach the UI.")
        self.store.save(incident, NOW)
        self.store.ingest(json.loads(FIXTURE.read_text()), NOW)

    def test_reconnect_frames_are_ordered_concise_and_complete(self):
        frames = reconnect_frames(self.store, "fixture-incident-001", NOW)
        self.assertEqual(len(frames), 3)
        self.assertTrue(frames[0].startswith("event: aster.progress\ndata: "))
        self.assertTrue(frames[1].startswith("event: aster.incident\ndata: "))
        self.assertEqual(frames[2], "data: [DONE]\n\n")
        event = json.loads(frames[1].split("data: ", 1)[1])
        self.assertEqual(event["evidence"][0]["age_seconds"], 120)
        self.assertEqual(event["next"]["state"], "proposed_read_only")

    def test_raw_facts_and_hypotheses_are_not_presented(self):
        rendered = "".join(reconnect_frames(self.store, "fixture-incident-001", NOW))
        self.assertNotIn("response_cap", rendered)
        self.assertNotIn("internal hypothesis", rendered)
        self.assertNotIn("facts", rendered)
        self.assertNotIn("hypotheses", rendered)

    def test_untrusted_text_is_not_forwarded_to_presentation(self):
        snapshot = self.store.reconnect_snapshot("fixture-incident-001", NOW)
        incident = snapshot["incident"]
        incident["title"] = "private-title-marker"
        incident["incident_id"] = "private-incident-marker"
        incident["observations"][0]["summary"] = "private-summary-marker"
        incident["observations"][0]["source"] = "private-source-marker"
        incident["observations"][0]["evidence_id"] = "private-evidence-marker"
        incident["next"]["reason"] = "private-reason-marker"
        presentation = incident_presentation(snapshot)
        encoded = json.dumps(presentation)
        for marker in ("private-title-marker", "private-incident-marker", "private-summary-marker",
                       "private-source-marker", "private-evidence-marker",
                       "private-reason-marker"):
            self.assertNotIn(marker, encoded)
        self.assertEqual(presentation["schema_version"], 3)
        self.assertEqual(presentation["evidence"][0]["target"], "aster-gateway")

    def test_reconnect_frames_do_not_expose_arbitrary_incident_id(self):
        rendered = "".join(reconnect_frames(self.store, "fixture-incident-001", NOW))
        self.assertNotIn("fixture-incident-001", rendered)

    def test_next_step_does_not_copy_unknown_or_private_fields(self):
        snapshot = self.store.reconnect_snapshot("fixture-incident-001", NOW)
        snapshot["incident"]["next"]["private_note"] = "private-next-marker"
        snapshot["incident"]["next"]["execution"] = "private-execution-marker"
        rendered = json.dumps(incident_presentation(snapshot))
        self.assertNotIn("private-next-marker", rendered)
        self.assertNotIn("private-execution-marker", rendered)
        self.assertIn("not performed by the investigation loop", rendered)

    def test_next_step_rejects_unknown_route(self):
        snapshot = self.store.reconnect_snapshot("fixture-incident-001", NOW)
        snapshot["incident"]["next"]["target"] = "private-target-marker"
        with self.assertRaises(InvestigationError):
            incident_presentation(snapshot)

    def test_terminal_next_steps_use_fixed_explanations(self):
        snapshot = self.store.reconnect_snapshot("fixture-incident-001", NOW)
        for state in ("bounded", "sufficient_or_escalate"):
            snapshot["incident"]["next"] = {
                "state": state, "reason": "private-reason-marker", "extra": "private-extra-marker"
            }
            rendered = json.dumps(incident_presentation(snapshot))
            self.assertNotIn("private-reason-marker", rendered)
            self.assertNotIn("private-extra-marker", rendered)
            self.assertNotIn("target", json.dumps(incident_presentation(snapshot)["next"]))

    def test_pending_followup_is_presented_without_hypothesis_or_internal_id(self):
        incident = self.store.load("fixture-incident-001", NOW)
        self.store.bind_follow_up({
            "schema_version": 1,
            "incident_id": incident.incident_id,
            "state_digest": incident_state_digest(incident),
            "hypothesis_summary": "private-hypothesis-marker",
            "disposition": "observe",
            "target": "inference-server",
            "kind": "status",
        }, NOW)
        frames = reconnect_frames(self.store, incident.incident_id, NOW)
        rendered = "".join(frames)
        self.assertNotIn("private-hypothesis-marker", rendered)
        self.assertNotIn(incident.incident_id, rendered)
        event = json.loads(frames[1].split("data: ", 1)[1])
        self.assertEqual(event["follow_up"]["decision_count"], 1)
        self.assertEqual(event["follow_up"]["consumed_count"], 0)
        self.assertEqual(event["follow_up"]["pending"]["target"], "inference-server")

    def test_malformed_followup_presentation_fails_closed(self):
        snapshot = self.store.reconnect_snapshot("fixture-incident-001", NOW)
        with self.assertRaises(InvestigationError):
            incident_presentation(snapshot, {
                "state_digest": "0" * 64,
                "decision_count": 1,
                "consumed_count": 0,
                "pending": {"decision_ref": "safe", "disposition": "observe", "target": "private", "kind": "status"},
            })


if __name__ == "__main__":
    unittest.main()
