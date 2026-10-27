import copy
import json
import unittest
from datetime import datetime, timezone

from sysadmin_investigation import EvidenceRequest, InvestigationError, Observation, create_incident
from sysadmin_proposal_boundary import (
    accept_model_proposal,
    build_proposal_request,
    propose_follow_up,
)


NOW = datetime(2026, 10, 27, 8, 0, tzinfo=timezone.utc)


class ProposalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.incident = create_incident(
            "private-incident-identity",
            "Private household wording",
            [
                EvidenceRequest("aster-gateway", "status", "Check gateway state."),
                EvidenceRequest("inference-server", "status", "Check fixed inference health."),
            ],
        )
        self.incident.add_hypothesis("Private operator hypothesis.")
        self.incident.add_observation(
            Observation(
                evidence_id="private-evidence-identity",
                incident_id=self.incident.incident_id,
                target="aster-gateway",
                kind="status",
                observed_at="2026-10-27T07:59:00Z",
                source="private-source-name",
                state="ok",
                summary="The gateway is serving requests.",
                facts={"service": "aster-agent", "availability": "serving"},
            ),
            NOW,
        )

    def response(self, request=None, **changes):
        request = request or build_proposal_request(self.incident)
        value = {
            "schema_version": 1,
            "request_ref": request["request_ref"],
            "disposition": "observe",
            "hypothesis_summary": "Inference health may distinguish a downstream fault.",
            "target": "inference-server",
            "kind": "status",
            "evidence_refs": [request["observations"][0]["evidence_ref"]],
        }
        value.update(changes)
        return value

    def test_request_contains_only_sanitized_bounded_state(self):
        request = build_proposal_request(self.incident)
        self.assertEqual(
            {"schema_version", "request_ref", "observations", "remaining_checks",
             "allowed_dispositions", "constraints"},
            set(request),
        )
        encoded = json.dumps(request, sort_keys=True)
        for private in (
            self.incident.incident_id,
            self.incident.title,
            self.incident.hypotheses[0],
            self.incident.observations[0]["evidence_id"],
            self.incident.observations[0]["source"],
        ):
            self.assertNotIn(private, encoded)
        self.assertEqual(
            [{"target": "inference-server", "kind": "status",
              "reason": "Check fixed inference health."}],
            request["remaining_checks"],
        )
        self.assertEqual("none", request["constraints"]["authority"])
        self.assertEqual("none", request["constraints"]["effect"])

    def test_transport_is_injected_and_cannot_add_authority(self):
        seen = []

        def transport(request):
            seen.append(copy.deepcopy(request))
            return self.response(request)

        decision = propose_follow_up(self.incident, transport)
        self.assertEqual(1, len(seen))
        self.assertEqual("inference-server", decision["request"]["target"])
        self.assertEqual("not performed", decision["request"]["execution"])
        self.assertEqual("none", decision["authority"])
        self.assertEqual("none", decision["effect"])

    def test_stale_response_and_unavailable_citations_fail_closed(self):
        for changes in (
            {"request_ref": "proposal-0000000000000000"},
            {"evidence_refs": ["evidence-0000000000000000"]},
            {"evidence_refs": []},
            {"evidence_refs": [build_proposal_request(self.incident)["observations"][0]["evidence_ref"]] * 2},
        ):
            with self.subTest(changes=changes), self.assertRaises(InvestigationError):
                accept_model_proposal(self.incident, self.response(**changes))

    def test_every_exposed_observation_must_be_cited(self):
        incident = copy.deepcopy(self.incident)
        incident.add_observation(Observation(
            evidence_id="private-inference-evidence",
            incident_id=incident.incident_id,
            target="inference-server",
            kind="status",
            observed_at="2026-10-27T07:59:10Z",
            source="private-source-name",
            state="ok",
            summary="The inference endpoint is healthy.",
            facts={"service": "aster-llama"},
        ), NOW)
        request = build_proposal_request(incident)
        response = {
            "schema_version": 1,
            "request_ref": request["request_ref"],
            "disposition": "complete",
            "hypothesis_summary": "The bounded status evidence supports a conclusion.",
            "target": None,
            "kind": None,
            "evidence_refs": [request["observations"][1]["evidence_ref"]],
        }
        with self.assertRaisesRegex(InvestigationError, "all available"):
            accept_model_proposal(incident, response)
        response["evidence_refs"] = [item["evidence_ref"] for item in request["observations"]]
        self.assertEqual("complete", accept_model_proposal(incident, response)["disposition"])

    def test_unplanned_or_terminal_target_fails_closed(self):
        cases = (
            {"target": "aster-gateway", "kind": "log"},
            {"target": "aster-gateway", "kind": "status"},
            {"disposition": "complete", "target": "inference-server", "kind": "status"},
            {"disposition": "escalate", "target": None, "kind": "status"},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(InvestigationError):
                accept_model_proposal(self.incident, self.response(**changes))

    def test_terminal_proposal_is_effect_free_and_cited(self):
        decision = accept_model_proposal(
            self.incident,
            self.response(
                disposition="complete",
                target=None,
                kind=None,
                hypothesis_summary="The available status evidence supports a bounded conclusion.",
            ),
        )
        self.assertEqual("complete", decision["disposition"])
        self.assertIsNone(decision["request"])
        self.assertEqual("none", decision["authority"])
        self.assertEqual("none", decision["effect"])

    def test_exhausted_unavailable_evidence_can_only_escalate(self):
        incident = create_incident(
            "private-unavailable-incident",
            "Private unavailable report",
            [EvidenceRequest("aster-gateway", "status", "Check gateway state.")],
        )
        incident.add_observation(Observation(
            evidence_id="private-unavailable-evidence",
            incident_id=incident.incident_id,
            target="aster-gateway",
            kind="status",
            observed_at="2026-10-27T07:59:00Z",
            source="private-source-name",
            state="unavailable",
            summary="The registered source was unavailable.",
            facts={},
        ), NOW)
        request = build_proposal_request(incident)
        self.assertEqual(["escalate"], request["allowed_dispositions"])
        response = {
            "schema_version": 1,
            "request_ref": request["request_ref"],
            "disposition": "complete",
            "hypothesis_summary": "The evidence is unavailable.",
            "target": None,
            "kind": None,
            "evidence_refs": [request["observations"][0]["evidence_ref"]],
        }
        with self.assertRaisesRegex(InvestigationError, "disposition"):
            accept_model_proposal(incident, response)
        response["disposition"] = "escalate"
        self.assertEqual("escalate", accept_model_proposal(incident, response)["disposition"])

    def test_effect_claims_malformed_shapes_and_extra_fields_fail_closed(self):
        malformed = [
            self.response(hypothesis_summary="I restarted the service and fixed it."),
            self.response(schema_version=True),
            self.response(disposition="repair"),
            self.response(hypothesis_summary=""),
            self.response(evidence_refs="evidence-ref"),
        ]
        extra = self.response()
        extra["authority"] = "repair"
        malformed.append(extra)
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(InvestigationError):
                accept_model_proposal(self.incident, value)

    def test_response_is_rebound_to_current_private_identity(self):
        request = build_proposal_request(self.incident)
        response = self.response(request)
        changed = copy.deepcopy(self.incident)
        changed.add_hypothesis("A newer private hypothesis.")
        with self.assertRaisesRegex(InvestigationError, "stale model proposal"):
            accept_model_proposal(changed, response)

    def test_initial_incident_can_select_first_check_without_citation(self):
        incident = create_incident(
            "private-initial-incident",
            "Private initial report",
            [EvidenceRequest("aster-gateway", "status", "Check gateway state.")],
        )
        request = build_proposal_request(incident)
        response = {
            "schema_version": 1,
            "request_ref": request["request_ref"],
            "disposition": "observe",
            "hypothesis_summary": "Gateway state is the first bounded discriminator.",
            "target": "aster-gateway",
            "kind": "status",
            "evidence_refs": [],
        }
        decision = accept_model_proposal(incident, response)
        self.assertEqual("aster-gateway", decision["request"]["target"])


if __name__ == "__main__":
    unittest.main()
