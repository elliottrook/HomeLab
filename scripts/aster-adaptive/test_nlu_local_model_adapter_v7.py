import json
import hashlib
from pathlib import Path
import unittest

import nlu_local_model_adapter_v7 as candidate


class CandidateV7Tests(unittest.TestCase):
    def test_payload_is_deterministic_tool_free_and_non_authorizing(self):
        raw = candidate.build_payload("Restart the named test service")
        self.assertEqual(raw, candidate.build_payload("Restart the named test service"))
        value = json.loads(raw)
        self.assertNotIn("tools", value)
        self.assertEqual(0, value["temperature"])
        self.assertFalse(value["stream"])
        self.assertIn("grants no authority", candidate.SYSTEM_POLICY)

    def test_v7_names_change_and_privacy_edges(self):
        self.assertIn("named restart", candidate.SYSTEM_POLICY)
        self.assertIn("another person's thoughts", candidate.SYSTEM_POLICY)
        self.assertIn("erase or purge audit history", candidate.SYSTEM_POLICY)
        self.assertIn("does not reduce sensitivity", candidate.SYSTEM_POLICY)

    def test_tracked_policy_matches_exact_prompt_and_schema(self):
        path = Path(__file__).parent / "fixtures" / "nlu-local-model-policy-v7.json"
        value = json.loads(path.read_text())
        self.assertEqual(candidate.SYSTEM_POLICY, value["system_policy"])
        self.assertEqual(candidate.RESPONSE_SCHEMA, value["response_schema"])
        self.assertEqual(
            "180f0df3fd018a5cb4a2362a4fa454562aad973ba80b6f11f4f06c1477ec6b4d",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
