from __future__ import annotations

import urllib.error
import unittest
from pathlib import Path
from unittest.mock import patch

import nlu_joint_semantic_35b_v1 as candidate
import nlu_whole_label_public_runner_v1 as runner


FIXTURE = Path(__file__).with_name("nlu-development-v1.json")


class PublicRunnerFailureTests(unittest.TestCase):
    def test_http_4xx_is_bounded_and_stops_after_first_case(self):
        class Opener:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(
                    request.full_url, 400, "bad request", {}, None)

        with patch.object(runner.urllib.request, "build_opener", return_value=Opener()):
            value = runner.run(
                FIXTURE.read_bytes(), "x" * 32,
                endpoint=candidate.PUBLIC_GATE_ENDPOINT,
                implementation=candidate,
                candidate_name="joint-semantic-35b-v1")
        self.assertEqual(1, value["attempted"])
        self.assertEqual(0, value["valid"])
        self.assertEqual("http_4xx", value["records"][0]["failure"])
        self.assertNotIn("bad request", str(value))


if __name__ == "__main__":
    unittest.main()
