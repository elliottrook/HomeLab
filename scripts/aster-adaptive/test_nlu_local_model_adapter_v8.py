import json
import hashlib
from pathlib import Path
import unittest

import nlu_local_model_adapter_v8 as candidate


class CandidateV8Tests(unittest.TestCase):
    def test_payload_remains_tool_free_and_non_authorizing(self):
        raw = candidate.build_payload("Patch the sample and erase its rollback copy")
        self.assertEqual(raw, candidate.build_payload(
            "Patch the sample and erase its rollback copy"
        ))
        value = json.loads(raw)
        self.assertNotIn("tools", value)
        self.assertEqual(0, value["temperature"])
        self.assertIn("grants no authority", candidate.SYSTEM_POLICY)

    def test_v8_names_measured_safety_and_capability_edges(self):
        for text in (
            "only rollback or recovery copy",
            "retain the capability category",
            "Negated actions",
            "Comparing two local or private sources adds local.join",
            "corrects itself to inspection",
        ):
            self.assertIn(text, candidate.SYSTEM_POLICY)

    def test_tracked_policy_matches_exact_prompt_and_schema(self):
        path = Path(__file__).parent / "fixtures" / "nlu-local-model-policy-v8.json"
        value = json.loads(path.read_text())
        self.assertEqual(candidate.SYSTEM_POLICY, value["system_policy"])
        self.assertEqual(candidate.RESPONSE_SCHEMA, value["response_schema"])
        self.assertEqual(
            "6fcdb80ded087c138003d4ab9d4172617f465c90ff8f0325db3d48ae4126ce5e",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
