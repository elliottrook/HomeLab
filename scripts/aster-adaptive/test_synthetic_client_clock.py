"""Fictional in-process tests; these do not measure live Aster or Companion."""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aster_asgi_clock import ASGIResponseClock
from synthetic_client_clock import run_fixture

ID = "a" * 32
BODY = b"fictional answer only"


class Fixture:
    synthetic_clock_fixture = True

    def __init__(self, *, partial=False, size=0):
        self.partial = partial
        self.size = size

    async def __call__(self, scope, receive, send):
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body",
                    "body": b"x" * self.size if self.size else BODY,
                    "more_body": self.partial})
        if self.partial:
            raise RuntimeError("fictional interrupted stream")


class ClockPairTests(unittest.TestCase):
    def run_pair(self, app, display):
        ticks = iter([1_000_000_000, 1_050_000_000])
        return asyncio.run(run_fixture(
            ASGIResponseClock(app, [], id_factory=lambda: ID),
            display, clock=lambda: next(ticks)))

    def test_complete_display_joins_without_claiming_usefulness(self):
        seen = []
        row = self.run_pair(Fixture(), seen.append)
        self.assertEqual(seen, [BODY])
        self.assertEqual(row["fixture_state"], "displayed")
        self.assertEqual(row["client"]["accepted_to_displayed_ms"], 50.0)
        self.assertTrue(row["joined"]["terminal_joined"])
        self.assertIsNone(row["joined"]["useful_answer_ms"])
        self.assertNotIn(BODY.decode(), str(row))

    def test_renderer_failure_is_censored_even_after_gateway_terminal(self):
        def fail(_body):
            raise RuntimeError("fictional renderer detail")

        row = self.run_pair(Fixture(), fail)
        self.assertEqual(row["fixture_state"], "failed")
        self.assertTrue(row["gateway"]["terminal_observed"])
        self.assertTrue(row["joined"]["censored"])
        self.assertIsNone(row["client"]["accepted_to_displayed_ms"])
        self.assertNotIn("renderer detail", str(row))

    def test_partial_response_is_censored_and_never_displayed(self):
        seen = []
        row = self.run_pair(Fixture(partial=True), seen.append)
        self.assertEqual(seen, [])
        self.assertFalse(row["gateway"]["terminal_observed"])
        self.assertTrue(row["joined"]["censored"])
        self.assertNotIn("interrupted stream", str(row))

    def test_oversized_response_is_not_returned_or_marked_displayed(self):
        row = self.run_pair(Fixture(size=65_537), lambda _: None)
        self.assertEqual(row["fixture_state"], "failed")
        self.assertTrue(row["joined"]["censored"])
        self.assertLess(len(str(row)), 1500)

    def test_async_renderer_cannot_falsely_mark_display(self):
        async def fake_display(_body):
            pass

        row = self.run_pair(Fixture(), fake_display)
        self.assertEqual(row["fixture_state"], "failed")
        self.assertTrue(row["joined"]["censored"])

    def test_unmarked_app_rejected_before_invocation(self):
        calls = []

        async def unmarked(scope, receive, send):
            calls.append(True)

        with self.assertRaisesRegex(ValueError, "marked in-process"):
            self.run_pair(unmarked, lambda _: None)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
