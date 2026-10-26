import hashlib
import json
from pathlib import Path
import unittest

import nlu_local_model_adapter_v10 as candidate


class CandidateV10Tests(unittest.TestCase):
    def test_payload_remains_tool_free_and_non_authorizing(self):
        raw = candidate.build_payload("Inspect the synthetic record")
        self.assertEqual(raw, candidate.build_payload("Inspect the synthetic record"))
        value = json.loads(raw)
        self.assertNotIn("tools", value)
        self.assertEqual(0, value["temperature"])
        self.assertIn("grants no authority", candidate.SYSTEM_POLICY)

    def test_v10_names_measured_precision_rules(self):
        for text in (
            "assign only capabilities required",
            "explicit timer operation",
            "private facts already supplied",
            "corrected final intent to inspect",
            "Do not invent capabilities",
        ):
            self.assertIn(text, candidate.SYSTEM_POLICY)

    def test_tracked_policy_matches_exact_prompt_and_schema(self):
        path = Path(__file__).parent / "fixtures" / "nlu-local-model-policy-v10.json"
        value = json.loads(path.read_text())
        self.assertEqual(candidate.SYSTEM_POLICY, value["system_policy"])
        self.assertEqual(candidate.RESPONSE_SCHEMA, value["response_schema"])
        self.assertEqual("8763186780060f6602db6d8632fa4723a1173d82a3c738a211c22f6d7ebe4b8d", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
