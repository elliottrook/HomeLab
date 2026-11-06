import copy
import unittest

import nlu_k2_development_scorer_v1 as scorer
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)
ROUTE = next(label_id for label_id, value in ontology.CATALOGUE.items()
             if value["disposition"] == "route")
NONROUTE = next(label_id for label_id, value in ontology.CATALOGUE.items()
                if value["disposition"] != "route")


def arbitration(case_id, label_id, shortlist=None):
    shortlist = shortlist or ([label_id] + [item for item in LABELS
                                            if item != label_id][:3])
    return {
        "case_id": case_id,
        "shortlist_ids": shortlist,
        "selected_label_id": label_id,
        "guard_changed": False,
        "interpretation": copy.deepcopy(ontology.CATALOGUE[label_id]),
        "latency_seconds": 0.5,
        "authority": "not-granted",
    }


class K2DevelopmentScorerTests(unittest.TestCase):
    def test_passing_floor(self):
        truth = {f"case-{index}": ROUTE for index in range(116)}
        records = [arbitration(case_id, ROUTE) for case_id in truth]
        summary = scorer.score_rows(
            truth, records, model_requests=116, retries=0, response_errors=0)
        self.assertEqual("pass", summary["status"])
        self.assertTrue(summary["development_gate_passed"])

    def test_error_rate_and_safety_fail_closed(self):
        truth = {f"case-{index}": ROUTE for index in range(116)}
        records = [arbitration(case_id, ROUTE) for case_id in truth]
        for index in range(12):
            case_id = f"case-{index}"
            records[index] = arbitration(case_id, NONROUTE)
        summary = scorer.score_rows(
            truth, records, model_requests=116, retries=0, response_errors=0)
        self.assertEqual("reject", summary["status"])
        self.assertGreater(summary["accepted_error_rate"], 0.10)

        truth = {f"case-{index}": NONROUTE for index in range(116)}
        records = [arbitration(case_id, NONROUTE) for case_id in truth]
        records[0] = arbitration("case-0", ROUTE)
        summary = scorer.score_rows(
            truth, records, model_requests=116, retries=0, response_errors=0)
        self.assertEqual(1, summary["unsafe_false_routes"])
        self.assertEqual("reject", summary["status"])

    def test_model_count_retry_or_response_error_rejected(self):
        truth = {"case-1": ROUTE}
        records = [arbitration("case-1", ROUTE)]
        for kwargs in (
            {"model_requests": 0, "retries": 0, "response_errors": 0},
            {"model_requests": 1, "retries": 1, "response_errors": 0},
            {"model_requests": 1, "retries": 0, "response_errors": 1},
        ):
            with self.assertRaises(ValueError):
                scorer.score_rows(truth, records, **kwargs)

    def test_duplicate_or_missing_decision_rejected(self):
        truth = {"case-1": ROUTE, "case-2": ROUTE}
        duplicate = [arbitration("case-1", ROUTE),
                     arbitration("case-1", ROUTE)]
        with self.assertRaises(ValueError):
            scorer.score_rows(truth, duplicate, model_requests=2,
                              retries=0, response_errors=0)


if __name__ == "__main__":
    unittest.main()
