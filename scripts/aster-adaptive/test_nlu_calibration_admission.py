import unittest

from nlu_calibration_admission import FAMILIES, admit


POLICY = {
    "minimum_calibration_cases": 60,
    "minimum_cases_per_family": {family: 10 for family in FAMILIES},
    "constraints": {"minimum_coverage": 0.6, "max_unsafe_false_route": 0},
}


def labels(route_count=36):
    rows = []
    for family in FAMILIES:
        for number in range(10):
            index = len(rows)
            rows.append({"id": f"{family}-{number}", "family": family,
                         "label": {"disposition": "route" if index < route_count else "clarify"}})
    return rows


class NLUCalibrationAdmissionTests(unittest.TestCase):
    def test_accepts_balanced_feasible_calibration(self):
        result = admit(labels(), POLICY)
        self.assertTrue(result["feasible"])
        self.assertEqual("all-calibration-cases", result["coverage_denominator"])
        self.assertEqual(36, result["minimum_safe_route_targets"])
        self.assertEqual(36, result["safe_route_targets"])

    def test_rejects_mathematically_impossible_calibration(self):
        with self.assertRaisesRegex(ValueError, "cannot satisfy"):
            admit(labels(35), POLICY)

    def test_rejects_family_imbalance_even_when_total_is_large_enough(self):
        value = labels()
        value[0]["family"] = "general-answer"
        with self.assertRaisesRegex(ValueError, "change-request"):
            admit(value, POLICY)

    def test_rejects_duplicate_identity_and_policy_drift(self):
        value = labels()
        value[1]["id"] = value[0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicated"):
            admit(value, POLICY)
        changed = dict(POLICY)
        changed["other"] = True
        with self.assertRaisesRegex(ValueError, "policy differs"):
            admit(labels(), changed)


if __name__ == "__main__":
    unittest.main()
