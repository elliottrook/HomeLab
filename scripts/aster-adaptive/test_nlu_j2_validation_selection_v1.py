import copy
import unittest

import nlu_j2_validation_selection_v1 as selection


def summaries():
    return [{"epoch": epoch, "rows": 192, "raw_exact_count": 150,
             "guarded_exact_count": 145,
             "mean_validation_loss": round(1.0 / epoch, 12)}
            for epoch in range(1, 41)]


def records():
    return [{"id": f"case-{index:03d}",
             "margin": 0.8 if index < 120 else 0.1,
             "raw_exact": index < 120, "guarded_exact": index < 120}
            for index in range(192)]


class J2ValidationSelectionTests(unittest.TestCase):
    def test_checkpoint_tie_break_order_is_exact(self):
        rows = summaries(); rows[10]["guarded_exact_count"] = 146
        rows[10]["raw_exact_count"] = 149
        rows[20]["guarded_exact_count"] = 146
        rows[20]["raw_exact_count"] = 151
        self.assertEqual(21, selection.select_epoch(rows))
        rows[10]["raw_exact_count"] = 151
        rows[10]["mean_validation_loss"] = rows[20]["mean_validation_loss"]
        self.assertEqual(11, selection.select_epoch(rows))

    def test_threshold_rejects_inexact_low_margin_rows_and_maximizes_coverage(self):
        value = selection.select_threshold(records())
        self.assertEqual(120, value["accepted"])
        self.assertEqual(0.105, value["threshold"])
        self.assertFalse(value["evaluation_inputs_used"])

    def test_no_threshold_with_minimum_coverage_fails_closed(self):
        rows = records()
        for row in rows[110:]: row["raw_exact"] = row["guarded_exact"] = False
        with self.assertRaisesRegex(ValueError, "no eligible"):
            selection.select_threshold(rows)

    def test_missing_duplicate_nonfinite_and_precision_drift_fail(self):
        rows = summaries(); rows.pop()
        with self.assertRaises(ValueError): selection.select_epoch(rows)
        rows = summaries(); rows[1]["epoch"] = 1
        with self.assertRaises(ValueError): selection.select_epoch(rows)
        rows = summaries(); rows[0]["mean_validation_loss"] = float("nan")
        with self.assertRaises(ValueError): selection.select_epoch(rows)
        rows = records(); rows[1]["id"] = rows[0]["id"]
        with self.assertRaises(ValueError): selection.select_threshold(rows)


if __name__ == "__main__": unittest.main()
