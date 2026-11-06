import unittest

import nlu_k2_route_selector_v1 as selector
import nlu_whole_label_choice_v1 as ontology


def label(family, sensitivity=None):
    for value in ontology.CATALOGUE.values():
        if value["request_family"] == family and value["disposition"] == "route":
            if sensitivity is None or value["sensitivity"] == sensitivity:
                return value
    raise AssertionError("fixture label unavailable")


class K2RouteSelectorTests(unittest.TestCase):
    def select(self, value):
        return selector.select(request_id="shadow-1", principal_ref="shadow-user",
                               interpretation=value, now=100)

    def test_read_only_and_public_research_propose_read_only_codex(self):
        values = (label("read-only-investigation", "internal"),
                  label("external-research", "public"))
        for value in values:
            interpretation, route = self.select(value)
            self.assertEqual("codex", route["status"])
            self.assertEqual("codex-subscription-readonly", route["backend_id"])
            self.assertEqual("cloud", route["egress"])
            self.assertEqual("not-granted", route["authorization"])
            self.assertEqual(interpretation["policy_digest"], route["policy_digest"])

    def test_personal_data_never_proposes_cloud(self):
        for family in ("read-only-investigation", "external-research"):
            _, route = self.select(label(family, "personal"))
            self.assertEqual("local", route["status"])
            self.assertEqual("local", route["egress"])
            self.assertEqual("aster-local-private", route["backend_id"])

    def test_other_routable_families_stay_local(self):
        for family in ("general-answer", "household-command", "change-request"):
            _, route = self.select(label(family))
            self.assertEqual("local", route["status"])
            self.assertEqual("aster-local", route["backend_id"])
            self.assertEqual("not-granted", route["authorization"])

    def test_nonroute_dispositions_stay_nonroutes(self):
        for disposition in ("clarify", "abstain", "deny"):
            value = next(item for item in ontology.CATALOGUE.values()
                         if item["disposition"] == disposition)
            _, route = self.select(value)
            self.assertEqual(disposition, route["status"])
            self.assertIsNone(route["backend_id"])
            self.assertEqual("none", route["egress"])

    def test_ttl_and_semantic_drift_fail_closed(self):
        with self.assertRaises(ValueError):
            selector.select(request_id="shadow-1", principal_ref="shadow-user",
                            interpretation=label("general-answer"), now=100,
                            ttl_seconds=301)
        changed = dict(label("general-answer")); changed["disposition"] = "deny"
        with self.assertRaises(ValueError):
            self.select(changed)


if __name__ == "__main__":
    unittest.main()
