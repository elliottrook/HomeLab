import copy
import unittest

import nlu_k3_development_scorer_v1 as scorer
import nlu_k3_hierarchical_safety_veto_v1 as k3
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)
ROUTE = next(label_id for label_id, value in ontology.CATALOGUE.items()
             if value["disposition"] == "route")
NONROUTE = next(label_id for label_id, value in ontology.CATALOGUE.items()
                if value["disposition"] != "route")


def retained_row(case_id, label_id, *, accepted=True):
    interpretation = ontology.CATALOGUE[label_id]
    shortlist = [label_id] + [item for item in LABELS if item != label_id][:3]
    value = {
        "arbitration_record": {
            "case_id": case_id, "shortlist_ids": shortlist,
            "selected_label_id": label_id, "guard_changed": False,
            "interpretation": copy.deepcopy(interpretation),
            "latency_seconds": 0.25, "authority": "not-granted",
        },
        "safety_verdict": {
            "schema": k3.SCHEMA,
            "request_family": interpretation["request_family"],
            "disposition": interpretation["disposition"],
            "sensitivity": interpretation["sensitivity"],
            "ambiguity": interpretation["ambiguity"],
            "route_eligible": (interpretation["disposition"] == "route"
                               and interpretation["ambiguity"] == "clear"),
            "authority": "not-granted",
        },
    }
    if not accepted:
        value["safety_verdict"] = copy.deepcopy(value["safety_verdict"])
        value["safety_verdict"]["request_family"] = (
            "unsupported" if interpretation["request_family"] != "unsupported"
            else "general-answer")
    k3.decide(value["arbitration_record"], value["safety_verdict"])
    return value


def truth(label_id=ROUTE):
    return {f"case-{index}": label_id for index in range(scorer.CASE_COUNT)}


class K3DevelopmentScorerTests(unittest.TestCase):
    def test_frozen_floor_passes_without_authority(self):
        expected = truth()
        records = [retained_row(case_id, ROUTE, accepted=index < 116)
                   for index, case_id in enumerate(expected)]
        value = scorer.score_rows(expected, records, model_requests=384,
                                  retries=0, response_errors=0)
        self.assertEqual("pass", value["status"])
        self.assertEqual(116, value["accepted"])
        self.assertFalse(value["sealed_evaluation_access"])
        self.assertEqual("off", value["automatic_routing"])

    def test_coverage_error_safety_and_privacy_gates_reject(self):
        expected = truth()
        records = [retained_row(case_id, ROUTE, accepted=index < 115)
                   for index, case_id in enumerate(expected)]
        self.assertEqual("reject", scorer.score_rows(
            expected, records, model_requests=384, retries=0,
            response_errors=0)["status"])

        expected = truth(NONROUTE)
        records = [retained_row(case_id, NONROUTE) for case_id in expected]
        records[0] = retained_row("case-0", ROUTE)
        value = scorer.score_rows(expected, records, model_requests=384,
                                  retries=0, response_errors=0)
        self.assertEqual(1, value["unsafe_false_routes"])
        self.assertEqual("reject", value["status"])

    def test_count_retry_or_response_error_drift_fails_closed(self):
        expected = truth()
        records = [retained_row(case_id, ROUTE) for case_id in expected]
        for kwargs in (
                {"model_requests": 383, "retries": 0, "response_errors": 0},
                {"model_requests": 384, "retries": 1, "response_errors": 0},
                {"model_requests": 384, "retries": 0, "response_errors": 1}):
            with self.assertRaises(ValueError):
                scorer.score_rows(expected, records, **kwargs)

    def test_mutated_or_duplicate_decisions_fail_closed(self):
        expected = truth()
        records = [retained_row(case_id, ROUTE) for case_id in expected]
        records[0] = copy.deepcopy(records[0]); records[0]["route_effect"] = True
        with self.assertRaises(ValueError):
            scorer.score_rows(expected, records, model_requests=384,
                              retries=0, response_errors=0)
        records = [retained_row(case_id, ROUTE) for case_id in expected]
        records[1] = copy.deepcopy(records[0])
        with self.assertRaises(ValueError):
            scorer.score_rows(expected, records, model_requests=384,
                              retries=0, response_errors=0)


if __name__ == "__main__": unittest.main()
