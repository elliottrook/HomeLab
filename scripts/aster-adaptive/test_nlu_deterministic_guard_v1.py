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


if __name__ == "__main__":
    unittest.main()
