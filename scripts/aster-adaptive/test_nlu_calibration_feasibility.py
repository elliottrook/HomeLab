import unittest

from nlu_calibration_feasibility import assess


def rows(route_count, total=60):
    return [
        {"id": f"C-{index:02d}", "label": {
            "disposition": "route" if index < route_count else "clarify",
        }}
        for index in range(total)
    ]


class CalibrationFeasibilityTests(unittest.TestCase):
    def test_rejects_impossible_zero_unsafe_calibration(self):
        result = assess(rows(30), {
            "minimum_coverage": 0.6,
            "max_unsafe_false_route": 0,
        })
        self.assertFalse(result["feasible"])
        self.assertEqual(36, result["required_routed"])
        self.assertEqual(30, result["maximum_routed_within_unsafe_limit"])

    def test_accepts_exactly_feasible_calibration(self):
        result = assess(rows(36), {
            "minimum_coverage": 0.6,
            "max_unsafe_false_route": 0,
        })
        self.assertTrue(result["feasible"])
        self.assertEqual(0.6, result["maximum_coverage_within_unsafe_limit"])

    def test_unsafe_allowance_counts_toward_maximum(self):
        result = assess(rows(35), {
            "minimum_coverage": 0.6,
            "max_unsafe_false_route": 1,
        })
        self.assertTrue(result["feasible"])

    def test_rejects_bad_constraints(self):
        with self.assertRaisesRegex(ValueError, "minimum coverage"):
            assess(rows(36), {"minimum_coverage": 0, "max_unsafe_false_route": 0})


if __name__ == "__main__":
    unittest.main()
