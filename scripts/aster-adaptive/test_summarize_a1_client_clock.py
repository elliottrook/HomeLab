"""Content-free A1 timing summary fixtures."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from summarize_a1_client_clock import summarize


def row(case_id: str, milliseconds: float | None, error_code=None) -> bytes:
    return (json.dumps({
        "case_id": case_id,
        "clock": {"schema_version": "aster-client-clock.v0",
                  "observation_id": "a" * 32 if milliseconds is not None else None,
                  "http_status": 200 if milliseconds is not None else None,
                  "accepted_to_displayed_ms": milliseconds,
                  "terminal_displayed": milliseconds is not None},
        "error_code": error_code,
    }, sort_keys=True) + "\n").encode()


class A1ClockSummaryTests(unittest.TestCase):
    def test_partial_run_keeps_censored_and_missing_denominators(self):
        raw = row("fictional-01", 100.0) + row("fictional-02", None, "client_exception")
        result = summarize(raw)
        self.assertEqual((result["observed_attempts"], result["not_observed"],
                          result["displayed"], result["censored"]), (2, 18, 1, 1))
        self.assertEqual(result["displayed_p95_ms"], 100.0)
        self.assertIsNone(result["useful_answer_ms"])
        self.assertNotIn("fictional-01", json.dumps(result))

    def test_twenty_displayed_uses_nearest_rank_p95(self):
        raw = b"".join(row(f"fictional-{index:02d}", float(index)) for index in range(1, 21))
        result = summarize(raw)
        self.assertEqual((result["displayed_median_ms"], result["displayed_p95_ms"],
                          result["displayed_max_ms"]), (10.5, 19.0, 20.0))
        self.assertEqual(result["not_observed"], 0)

    def test_extra_content_and_duplicate_identity_fail_closed(self):
        bad = json.loads(row("fictional-01", 10.0))
        bad["answer"] = "should never leave private custody"
        with self.assertRaisesRegex(ValueError, "unexpected"):
            summarize((json.dumps(bad) + "\n").encode())
        with self.assertRaisesRegex(ValueError, "repeated"):
            summarize(row("fictional-01", 10.0) * 2)

    def test_invalid_censored_state_and_oversized_file_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "invalid A1 client clock"):
            summarize(row("fictional-01", None))
        with self.assertRaisesRegex(ValueError, "size"):
            summarize(b"x" * 40_001)


if __name__ == "__main__":
    unittest.main()
