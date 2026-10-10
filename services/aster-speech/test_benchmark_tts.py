import json
import tempfile
import unittest
from pathlib import Path

from benchmark_tts import Fixture, Sample, load_fixtures, percentile, run, summarize


class FakeRenderer:
    name = "fake"
    load_seconds = 0.25

    def __init__(self):
        self.calls = 0
        self.closed = False

    def render(self, text):
        self.calls += 1
        return len(text) / 100, len(text) / 20

    def close(self):
        self.closed = True


class FixtureTests(unittest.TestCase):
    def test_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixtures.json"
            path.write_text(json.dumps([
                {"id": "same", "category": "one", "text": "hello"},
                {"id": "same", "category": "two", "text": "world"},
            ]))
            with self.assertRaises(ValueError):
                load_fixtures(path)

    def test_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixtures.json"
            path.write_text(json.dumps([
                {"id": "one", "category": "test", "text": "hello", "secret": "no"}
            ]))
            with self.assertRaises(ValueError):
                load_fixtures(path)


class BenchmarkTests(unittest.TestCase):
    def test_warmups_are_excluded_and_results_contain_no_text(self):
        renderer = FakeRenderer()
        fixtures = [Fixture("short", "test", "synthetic words")]
        samples = run(renderer, fixtures, warmups=2, iterations=3)
        self.assertEqual(renderer.calls, 5)
        self.assertEqual(len(samples), 3)
        self.assertNotIn("text", samples[0].__dict__)
        self.assertEqual(samples[0].fixture_id, "short")

    def test_nearest_rank_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0.5), 3)
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0.95), 5)

    def test_summary_calculates_latency_and_rtf(self):
        samples = [
            Sample("a", "test", 1, 1, 1.0, 2.0, 0.5),
            Sample("a", "test", 2, 1, 2.0, 2.0, 1.0),
            Sample("a", "test", 3, 1, 3.0, 2.0, 1.5),
        ]
        self.assertEqual(summarize(samples), {
            "synth_p50_seconds": 2.0,
            "synth_p95_seconds": 3.0,
            "rtf_p50": 1.0,
            "rtf_p95": 1.5,
        })


if __name__ == "__main__":
    unittest.main()
