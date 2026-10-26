import unittest

import nlu_ensemble_crossset_runner_v5 as runner
from nlu_threshold_policy import FAMILIES


def fold_rows(bad=False):
    rows = []
    for family_index, family in enumerate(FAMILIES):
        for index in range(10):
            route = index < 5
            rows.append({
                "id": f"{family_index}-{index}", "family": family,
                "decision_score": 0.9, "route_score": 0.9 if route else 0.0,
                "proposes_route": route,
                "accepted_decision_correct": not (bad and index == 9),
                "privacy_underclassified_if_routed": False,
                "unsafe_false_route_if_routed": False,
            })
    return rows


class NluEnsembleCrosssetRunnerV5Tests(unittest.TestCase):
    def test_six_stable_folds_pass_nested_selection(self):
        result = runner.nested_evaluate({f"v{i}": fold_rows() for i in range(1, 7)}, "a" * 64)
        self.assertEqual(6, len(result))
        self.assertTrue(all(row["status"] == "pass" for row in result))

    def test_outer_error_over_limit_fails_without_weakening_inner_policy(self):
        sets = {f"v{i}": fold_rows() for i in range(1, 7)}
        for row in sets["v6"][:7]:
            row["accepted_decision_correct"] = False
        result = runner.nested_evaluate(sets, "a" * 64)
        outer = next(row for row in result if row["outer"] == "v6")
        self.assertEqual("fail", outer["status"])
        self.assertGreater(outer["metrics"]["accepted_decision_error_rate"], 0.1)

    def test_outer_unsafe_route_fails(self):
        sets = {f"v{i}": fold_rows() for i in range(1, 7)}
        sets["v2"][0]["unsafe_false_route_if_routed"] = True
        result = runner.nested_evaluate(sets, "a" * 64)
        outer = next(row for row in result if row["outer"] == "v2")
        self.assertEqual("fail", outer["status"])
        self.assertEqual(1, outer["metrics"]["unsafe_false_route"])


if __name__ == "__main__":
    unittest.main()
