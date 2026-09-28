import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_incident_store import IncidentStore
from sysadmin_incident_stream import reconnect_frames
from sysadmin_investigation import EvidenceRequest, create_incident


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


if __name__ == "__main__":
    unittest.main()
