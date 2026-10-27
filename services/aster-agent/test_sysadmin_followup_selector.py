import copy
import unittest
from datetime import datetime, timezone

from sysadmin_followup_selector import incident_state_digest, select_follow_up
from sysadmin_investigation import (
    EvidenceRequest,
    Incident,
    InvestigationError,
    Observation,
    create_incident,
)


NOW = datetime(2026, 10, 27, 6, 0, tzinfo=timezone.utc)


class FollowUpSelectorTests(unittest.TestCase):
    def setUp(self):
        self.incident = create_incident(
            "incident-followup-001",
            "Aster response is incomplete",
            [
                EvidenceRequest("aster-gateway", "status", "Check gateway state."),
                EvidenceRequest("inference-server", "status", "Discriminate backend failure."),
                EvidenceRequest("aster-gateway", "log", "Inspect bounded gateway errors."),
            ],
        )
        self.incident.add_observation(
            Observation(
                evidence_id="evidence-gateway-status",
                incident_id=self.incident.incident_id,
                target="aster-gateway",
                kind="status",
                observed_at="2026-10-27T05:59:00Z",
                source="aster-gateway-status/v1",
                state="warn",
                summary="Gateway is reachable but dependency state is unknown.",
                facts={"service_state": "active"},
            ),
            NOW,
        )

    def proposal(self, **changes):
        value = {
            "schema_version": 1,
            "incident_id": self.incident.incident_id,
            "state_digest": incident_state_digest(self.incident),
            "hypothesis_summary": "The backend may be unavailable despite a healthy gateway.",
            "disposition": "observe",
            "target": "inference-server",
            "kind": "status",
        }
        value.update(changes)
        return value

    def test_selects_only_an_unfilled_preregistered_check(self):
        decision = select_follow_up(self.incident, self.proposal())
        self.assertEqual(decision["request"], {
            "target": "inference-server",
            "kind": "status",
            "reason": "Discriminate backend failure.",
            "execution": "not performed",
        })
        self.assertEqual(decision["authority"], "none")
        self.assertEqual(decision["effect"], "none")
        self.assertNotIn(self.incident.incident_id, str(decision["incident_ref"]))

    def test_selection_can_be_adaptive_within_the_plan(self):
        decision = select_follow_up(
            self.incident,
            self.proposal(
                hypothesis_summary="The gateway warning should be checked before the backend.",
                target="aster-gateway",
                kind="log",
            ),
        )
        self.assertEqual(decision["request"]["kind"], "log")

    def test_stale_or_cross_incident_proposal_fails_closed(self):
        for changes in (
            {"state_digest": "0" * 64},
            {"incident_id": "another-incident"},
        ):
            with self.subTest(changes=changes), self.assertRaises(InvestigationError):
                select_follow_up(self.incident, self.proposal(**changes))

    def test_observed_unplanned_or_malformed_selection_fails_closed(self):
        for changes in (
            {"target": "aster-gateway", "kind": "status"},
            {"target": "backup-catalog", "kind": "backup"},
            {"target": None},
            {"kind": []},
        ):
            with self.subTest(changes=changes), self.assertRaises(InvestigationError):
                select_follow_up(self.incident, self.proposal(**changes))

    def test_terminal_decisions_have_no_request_or_success_claim(self):
        for disposition in ("complete", "escalate"):
            decision = select_follow_up(
                self.incident,
                self.proposal(disposition=disposition, target=None, kind=None),
            )
            self.assertIsNone(decision["request"])
            self.assertNotIn("success", decision)
            self.assertEqual(decision["effect"], "none")

    def test_exact_shape_version_and_hypothesis_bounds(self):
        variants = []
        extra = self.proposal()
        extra["extra"] = True
        variants.append(extra)
        variants.append(self.proposal(schema_version=True))
        variants.append(self.proposal(state_digest="bad"))
        variants.append(self.proposal(hypothesis_summary=""))
        variants.append(self.proposal(hypothesis_summary="x" * 501))
        variants.append(self.proposal(disposition="repair"))
        for proposal in variants:
            with self.subTest(proposal=proposal), self.assertRaises(InvestigationError):
                select_follow_up(self.incident, proposal)

    def test_digest_changes_with_evidence_or_hypothesis_state(self):
        before = incident_state_digest(self.incident)
        changed = copy.deepcopy(self.incident)
        changed.add_hypothesis("A bounded revised hypothesis.")
        self.assertNotEqual(before, incident_state_digest(changed))

    def test_digest_is_stable_when_only_derived_observation_age_changes(self):
        before = incident_state_digest(self.incident)
        changed = copy.deepcopy(self.incident)
        changed.observations[0]["age_seconds"] += 3600
        self.assertEqual(before, incident_state_digest(changed))


if __name__ == "__main__":
    unittest.main()
