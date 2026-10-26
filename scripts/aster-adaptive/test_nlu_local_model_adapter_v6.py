import json
import unittest

import nlu_local_model_adapter_v6 as candidate


class CandidateV6Tests(unittest.TestCase):
    def test_payload_is_deterministic_tool_free_and_non_authorizing(self):
        raw = candidate.build_payload("Restart the named test service")
        self.assertEqual(raw, candidate.build_payload("Restart the named test service"))
        value = json.loads(raw)
        self.assertNotIn("tools", value)
        self.assertEqual(0, value["temperature"])
        self.assertFalse(value["stream"])
        self.assertIn("grants no authority", candidate.SYSTEM_POLICY)

    def test_v6_names_change_and_privacy_edges(self):
        self.assertIn("named restart", candidate.SYSTEM_POLICY)
        self.assertIn("another person's thoughts", candidate.SYSTEM_POLICY)


if __name__ == "__main__":
    unittest.main()
