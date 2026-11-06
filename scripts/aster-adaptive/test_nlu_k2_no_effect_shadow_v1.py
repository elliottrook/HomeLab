import copy
import hashlib
import unittest

import nlu_k2_no_effect_shadow_v1 as shadow
import nlu_k2_route_selector_v1 as selector
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


def fixture():
    rows = []
    by_family = {family: next((label_id for label_id, value in ontology.CATALOGUE.items()
                              if value["request_family"] == family), None)
                 for family in FAMILIES}
    for family in FAMILIES:
        label_id = by_family[family]
        value = ontology.CATALOGUE[label_id]
        for index in range(10):
            case_id = f"shadow-{family}-{index}"
            _, route = selector.select(request_id=case_id,
                                       principal_ref="shadow-principal",
                                       interpretation=value, now=1)
            rows.append({
                "id": case_id, "request_sha256": hashlib.sha256(case_id.encode()).hexdigest(),
                "expected_label_id": label_id, "final_label_id": label_id,
                "candidate_accepted": True, "route_status": route["status"],
                "backend_id": route["backend_id"], "egress": route["egress"],
                "baseline_status": "local", "latency_seconds": 1.0,
                "route_proposal_sha256": hashlib.sha256(selector.canonical(route)).hexdigest(),
            })
    value = {
        "schema": shadow.SCHEMA, "status": "sealed",
        "candidate_manifest_sha256": selector.ENGINE_SHA256,
        "selector_policy_sha256": selector.POLICY_SHA256,
        "source_class": "representative-sanitized-S0", "case_count": 60,
        "cases": rows, "model_requests": 60, "retries": 0,
        "response_errors": 0, "route_execution_attempted": False,
        "provider_egress_attempted": False, "external_cost_microunits": 0,
        "authority": "not-granted", "automatic_routing": "off",
        "release_sha256": "",
    }
    value["release_sha256"] = shadow.release_sha256(value)
    return value


class K2NoEffectShadowTests(unittest.TestCase):
    def test_balanced_exact_no_effect_shadow_passes(self):
        score = shadow.validate(fixture())
        self.assertEqual("pass", score["status"])
        self.assertEqual(60, score["accepted"])
        self.assertEqual(0, score["unsafe_false_routes"])
        self.assertFalse(score["route_execution_attempted"])

    def test_effect_egress_cost_or_content_fail_closed(self):
        for field, changed in (("route_execution_attempted", True),
                               ("provider_egress_attempted", True),
                               ("external_cost_microunits", 1)):
            value = fixture(); value[field] = changed
            value["release_sha256"] = shadow.release_sha256(value)
            with self.assertRaises(ValueError): shadow.validate(value)
        value = fixture(); value["cases"][0]["text"] = "forbidden"
        value["release_sha256"] = shadow.release_sha256(value)
        with self.assertRaises(ValueError): shadow.validate(value)

    def test_family_imbalance_and_digest_drift_fail_closed(self):
        value = fixture()
        value["cases"][0]["expected_label_id"] = value["cases"][10]["expected_label_id"]
        value["release_sha256"] = shadow.release_sha256(value)
        with self.assertRaisesRegex(ValueError, "family balance"):
            shadow.validate(value)
        value = fixture(); value["release_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "digest"):
            shadow.validate(value)

    def test_unaccepted_candidate_is_forced_to_abstain(self):
        value = fixture(); row = value["cases"][0]
        row.update(candidate_accepted=False, route_status="abstain",
                   backend_id=None, egress="none")
        value["release_sha256"] = shadow.release_sha256(value)
        score = shadow.validate(value)
        self.assertEqual(59, score["accepted"])
        changed = copy.deepcopy(value); changed["cases"][0]["route_status"] = "local"
        changed["release_sha256"] = shadow.release_sha256(changed)
        with self.assertRaisesRegex(ValueError, "route projection"):
            shadow.validate(changed)


if __name__ == "__main__":
    unittest.main()
