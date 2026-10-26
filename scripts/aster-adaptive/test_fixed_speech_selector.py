import unittest

from contracts import RequestInterpretation
from fixed_speech_selector import CAPABILITY, accept_answer, select_route


DIGEST = "sha256:" + "1" * 64


def interpretation(**changes):
    values = {
        "request_id": "speech-status-1",
        "principal_ref": "jason",
        "request_family": "read-only-investigation",
        "sensitivity": "internal",
        "capability_needs": (CAPABILITY,),
        "ambiguity": "clear",
        "disposition": "route",
        "reason": "understood",
        "engine_digest": DIGEST,
        "policy_digest": DIGEST,
    }
    values.update(changes)
    return RequestInterpretation(**values)


def result(state="ok", **changes):
    value = {
        "schema": 2,
        "capability": CAPABILITY,
        "observation": {
            "source": "homelab-doctor-catalogue/v3",
            "state": state,
            "observed_at": "2026-10-26T20:00:00Z",
            "age_seconds": 30,
            "facts": {} if state == "unavailable" else {"check_id": "aster.speech"},
        },
        "answer": "The fixed Speech observation is bounded and read only.",
        "authority": "not-granted",
    }
    value.update(changes)
    return value


class FixedSpeechSelectorTests(unittest.TestCase):
    def test_exact_internal_or_public_request_gets_local_proposal(self):
        for sensitivity in ("internal", "public"):
            with self.subTest(sensitivity=sensitivity):
                route = select_route(interpretation(sensitivity=sensitivity), now=100)
                self.assertEqual("local", route.status)
                self.assertEqual("aster-fixed-speech-caller", route.backend_id)
                self.assertEqual("local", route.egress)
                self.assertEqual("not-granted", route.authorization)
                self.assertEqual(130, route.expires_at)

    def test_selector_declines_broader_or_uncertain_interpretations(self):
        changes = (
            {"request_family": "general-answer"},
            {"sensitivity": "personal"},
            {"capability_needs": ()},
            {"capability_needs": (CAPABILITY, "repair.speech")},
            {"ambiguity": "ambiguous", "disposition": "clarify", "reason": "ambiguous"},
            {"disposition": "deny", "reason": "policy-denied"},
        )
        for change in changes:
            with self.subTest(change=change):
                self.assertIsNone(select_route(interpretation(**change), now=100))

    def test_route_ttl_is_bounded(self):
        for value in (0, 31, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_route(interpretation(), now=100, ttl_seconds=value)

    def test_answer_accepts_each_exact_state_and_retains_no_authority(self):
        item = interpretation()
        route = select_route(item, now=100)
        for state in ("ok", "warn", "fail", "unavailable"):
            with self.subTest(state=state):
                selected = accept_answer(item, route, result(state), now=101)
                self.assertEqual({"capability": CAPABILITY, "state": state}, selected["evidence"])
                self.assertEqual("not-granted", selected["authorization"])

    def test_answer_rejects_expired_or_drifted_route(self):
        item = interpretation()
        route = select_route(item, now=100, ttl_seconds=1)
        with self.assertRaisesRegex(ValueError, "expired"):
            accept_answer(item, route, result(), now=101)

    def test_answer_rejects_authority_identity_or_shape_drift(self):
        item = interpretation()
        route = select_route(item, now=100)
        bad = (
            result(authority="granted"),
            result(capability="diagnostic.other.latest"),
            result(schema=3),
            result(answer=""),
            result(observation={}),
        )
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                accept_answer(item, route, value, now=101)

    def test_answer_rejects_wrong_facts_age_or_source(self):
        item = interpretation()
        route = select_route(item, now=100)
        base = result()["observation"]
        changes = (
            {"facts": {}}, {"age_seconds": True}, {"age_seconds": 129601},
            {"source": "other"}, {"state": "unknown"},
        )
        for change in changes:
            value = result(observation=base | change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                accept_answer(item, route, value, now=101)


if __name__ == "__main__":
    unittest.main()
