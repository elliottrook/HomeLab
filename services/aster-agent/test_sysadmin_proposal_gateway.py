import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import EvidenceRequest, InvestigationError, Observation, create_incident
from sysadmin_proposal_boundary import build_proposal_request
from sysadmin_proposal_gateway import propose_and_bind_follow_up


NOW = datetime(2026, 10, 27, 8, 0, tzinfo=timezone.utc)


class ProposalGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        parent = Path(self.temp.name) / "state"
        parent.mkdir(mode=0o700)
        self.store = IncidentStore(parent / "incidents.sqlite3")
        self.incident = create_incident(
            "inc-fixture",
            "Private fixture title",
            [
                EvidenceRequest("aster-gateway", "status", "Check gateway state."),
                EvidenceRequest("inference-server", "status", "Check inference state."),
            ],
        )
        self.incident.add_observation(Observation(
            evidence_id="fixture-gateway-evidence",
            incident_id=self.incident.incident_id,
            target="aster-gateway",
            kind="status",
            observed_at="2026-10-27T07:59:00Z",
            source="fixture-source/v1",
            state="ok",
            summary="The gateway is serving.",
            facts={"availability": "serving"},
        ), NOW)
        self.store.save(self.incident, NOW)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def response(request, **changes):
        value = {
            "schema_version": 1,
            "request_ref": request["request_ref"],
            "disposition": "observe",
            "hypothesis_summary": "Inference status can distinguish a downstream fault.",
            "target": "inference-server",
            "kind": "status",
            "evidence_refs": [item["evidence_ref"] for item in request["observations"]],
        }
        value.update(changes)
        return value

    def test_valid_proposal_is_called_once_and_journaled_without_effect(self):
        calls = []

        def transport(request, api_key):
            calls.append((request, api_key))
            return self.response(request)

        result = propose_and_bind_follow_up(
            self.store, self.incident.incident_id, "fixture-secret", transport=transport, now=NOW
        )
        self.assertEqual(1, len(calls))
        self.assertEqual("fixture-secret", calls[0][1])
        self.assertEqual(1, result["decision_count"])
        self.assertEqual(0, result["consumed_count"])
        self.assertEqual("observe", result["pending"]["disposition"])
        self.assertEqual("inference-server", result["pending"]["target"])
        self.assertEqual(1, len(self.store.load(self.incident.incident_id, NOW).observations))

    def test_pending_decision_refuses_before_model_call(self):
        request = build_proposal_request(self.incident)
        decision = self.response(request)
        from sysadmin_proposal_boundary import accept_model_proposal
        trusted = accept_model_proposal(self.incident, decision)
        self.store.bind_follow_up({
            "schema_version": 1,
            "incident_id": self.incident.incident_id,
            "state_digest": trusted["bound_state_digest"],
            "hypothesis_summary": trusted["hypothesis_summary"],
            "disposition": trusted["disposition"],
            "target": trusted["request"]["target"],
            "kind": trusted["request"]["kind"],
        }, NOW)
        calls = []
        with self.assertRaisesRegex(InvestigationError, "pending"):
            propose_and_bind_follow_up(
                self.store, self.incident.incident_id, "fixture-secret",
                transport=lambda request, key: calls.append(request),
                now=NOW,
            )
        self.assertEqual([], calls)

    def test_state_change_during_model_call_rejects_stale_proposal(self):
        def transport(request, api_key):
            changed = self.store.load(self.incident.incident_id, NOW)
            changed.add_observation(Observation(
                evidence_id="fixture-inference-evidence",
                incident_id=changed.incident_id,
                target="inference-server",
                kind="status",
                observed_at="2026-10-27T07:59:10Z",
                source="fixture-source/v1",
                state="ok",
                summary="The inference endpoint is healthy.",
                facts={"availability": "serving"},
            ), NOW)
            self.store.save(changed, NOW)
            return self.response(request)

        with self.assertRaisesRegex(InvestigationError, "stale"):
            propose_and_bind_follow_up(
                self.store, self.incident.incident_id, "fixture-secret", transport=transport, now=NOW
            )
        self.assertIsNone(self.store.pending_follow_up(self.incident.incident_id, NOW))

    def test_invalid_response_creates_no_journal_entry(self):
        with self.assertRaisesRegex(InvestigationError, "fields"):
            propose_and_bind_follow_up(
                self.store,
                self.incident.incident_id,
                "fixture-secret",
                transport=lambda request, key: {"unexpected": True},
                now=NOW,
            )
        result = self.store.followup_journal_snapshot(self.incident.incident_id, NOW)
        self.assertEqual(0, result["decision_count"])
        self.assertIsNone(result["pending"])

    def test_missing_authentication_refuses_before_transport(self):
        calls = []
        with self.assertRaisesRegex(InvestigationError, "authentication"):
            propose_and_bind_follow_up(
                self.store, self.incident.incident_id, "",
                transport=lambda request, key: calls.append(request),
                now=NOW,
            )
        self.assertEqual([], calls)


if __name__ == "__main__":
    unittest.main()
