import unittest

import nlu_deterministic_guard_v1 as guard


def proposal(family="change-request", sensitivity="internal", capabilities=None):
    return {
        "request_family": family,
        "sensitivity": sensitivity,
        "capability_needs": capabilities or ["lab.change"],
        "ambiguity": "clear", "disposition": "route", "reason": "understood",
    }


class GuardTests(unittest.TestCase):
    def test_safety_disablement_is_denied(self):
        out = guard.apply("Disable the demo safety interlock", proposal("household-command", capabilities=["home.control"]))
        self.assertEqual(("deny", "policy-denied"), (out["disposition"], out["reason"]))

    def test_private_publication_is_denied(self):
        out = guard.apply("Post my private journal on the public forum", proposal("external-research", "personal", ["web.publish"]))
        self.assertEqual(("external-research", "deny", ["web.publish"]), (out["request_family"], out["disposition"], out["capability_needs"]))

    def test_impossible_request_abstains(self):
        out = guard.apply("Predict the imaginary never recorded result", proposal("household-command", capabilities=["home.control"]))
        self.assertEqual(("unsupported", "abstain", []), (out["request_family"], out["disposition"], out["capability_needs"]))

    def test_capabilities_are_minimal_and_canonical(self):
        out = guard.apply("Compare the official web report with the supplied note", proposal("external-research", "public", ["lab.read", "web.publish"]))
        self.assertEqual(["local.join", "web.read"], out["capability_needs"])

    def test_timer_requires_explicit_timer_operation(self):
        out = guard.apply("Run the demo fan for five minutes", proposal("household-command", capabilities=["timer.control", "home.control"]))
        self.assertEqual(["home.control"], out["capability_needs"])

    def test_family_capabilities_are_rebuilt_from_policy(self):
        out = guard.apply(
            "Inspect the server logs",
            proposal("read-only-investigation", capabilities=["lab.change", "web.read"]),
        )
        self.assertEqual(["lab.read"], out["capability_needs"])

    def test_personal_floor_never_trusts_public_proposal(self):
        out = guard.apply(
            "Summarize my medical appointment note",
            proposal("general-answer", "public", ["facts.answer"]),
        )
        self.assertEqual("personal", out["sensitivity"])

    def test_first_person_ownership_is_personal(self):
        out = guard.apply(
            "Explain my result",
            proposal("general-answer", "public", ["facts.answer"]),
        )
        self.assertEqual("personal", out["sensitivity"])

    def test_short_external_lookup_clarifies(self):
        out = guard.apply(
            "Find the latest one online",
            proposal("external-research", "public", ["web.read"]),
        )
        self.assertEqual(("clarify", "ambiguous"), (out["disposition"], out["reason"]))


if __name__ == "__main__":
    unittest.main()
