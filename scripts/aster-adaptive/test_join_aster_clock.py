import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from join_aster_clock import join

ID = "a" * 32


def client(**changes):
    item = {"schema_version": "aster-client-clock.v0", "observation_id": ID,
            "http_status": 200, "accepted_to_displayed_ms": 45.0,
            "terminal_displayed": True}
    item.update(changes)
    return item


def gateway(**changes):
    item = {"schema_version": "aster-asgi-clock.v0", "observation_id": ID,
            "path": "/v1/chat/completions", "http_status": 200,
            "first_body_ms": 12.0, "terminal_ms": 30.0,
            "terminal_observed": True}
    item.update(changes)
    return item


class ClockJoinTests(unittest.TestCase):
    def test_matching_terminal_observations_remain_not_yet_useful(self):
        item = join(client(), gateway())
        self.assertEqual(item["client_terminal_display_ms"], 45.0)
        self.assertEqual(item["gateway_terminal_ms"], 30.0)
        self.assertTrue(item["terminal_joined"])
        self.assertIsNone(item["useful_answer_ms"])

    def test_interrupted_stream_is_censored_even_if_client_saw_part(self):
        item = join(client(accepted_to_displayed_ms=None, terminal_displayed=False),
                    gateway(terminal_ms=None, terminal_observed=False))
        self.assertTrue(item["censored"])
        self.assertIsNone(item["client_terminal_display_ms"])
        self.assertIsNone(item["gateway_terminal_ms"])

    def test_gateway_completion_is_preserved_when_client_never_displays_it(self):
        item = join(client(accepted_to_displayed_ms=None, terminal_displayed=False),
                    gateway())
        self.assertFalse(item["terminal_joined"])
        self.assertTrue(item["censored"])
        self.assertIsNone(item["client_terminal_display_ms"])
        self.assertEqual(item["gateway_terminal_ms"], 30.0)

    def test_mismatch_or_content_payload_cannot_join(self):
        with self.assertRaisesRegex(ValueError, "identity"):
            join(client(observation_id="b" * 32), gateway())
        with self.assertRaisesRegex(ValueError, "raw content"):
            join(client(prompt="secret"), gateway())
        with self.assertRaisesRegex(ValueError, "status"):
            join(client(http_status=502), gateway())

    def test_invalid_timing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duration"):
            join(client(accepted_to_displayed_ms=float("nan")), gateway())
        with self.assertRaisesRegex(ValueError, "marker"):
            join(client(terminal_displayed=False), gateway())
        with self.assertRaisesRegex(ValueError, "marker"):
            join(client(), gateway(first_body_ms=40.0))


if __name__ == "__main__":
    unittest.main()
