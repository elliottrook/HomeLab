import hashlib
import json
from pathlib import Path
import unittest

import nlu_local_model_adapter_v9 as candidate


class CandidateV9Tests(unittest.TestCase):
    def test_payload_remains_tool_free_and_non_authorizing(self):
        raw = candidate.build_payload("Disable the synthetic safety control")
        self.assertEqual(raw, candidate.build_payload("Disable the synthetic safety control"))
        value = json.loads(raw)
        self.assertNotIn("tools", value)
        self.assertEqual(0, value["temperature"])
        self.assertIn("grants no authority", candidate.SYSTEM_POLICY)

    def test_v9_names_measured_failure_classes(self):
        for text in (
            "bypasses, defeats or removes a safety control",
            "publication of private or personal data to a public destination",
            "impossible, fictional-as-real, or unverifiable",
            "exact canonical order",
        ):
            self.assertIn(text, candidate.SYSTEM_POLICY)

    def test_tracked_policy_matches_exact_prompt_and_schema(self):
        path = Path(__file__).parent / "fixtures" / "nlu-local-model-policy-v9.json"
        value = json.loads(path.read_text())
        self.assertEqual(candidate.SYSTEM_POLICY, value["system_policy"])
        self.assertEqual(candidate.RESPONSE_SCHEMA, value["response_schema"])
        self.assertEqual("6672dc9209dda1b848a7e93be04264f34626fba8c2206cdfa0d798a828dc5953", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
