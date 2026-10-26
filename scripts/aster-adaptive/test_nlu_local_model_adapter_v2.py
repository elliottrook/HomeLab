import json
import unittest

import nlu_local_model_adapter_v2 as candidate


class CandidateV2Tests(unittest.TestCase):
    def test_route_is_explicitly_a_non_authorizing_label(self):
        self.assertIn("route is only a classification label", candidate.SYSTEM_POLICY)
        self.assertIn("grants no permission", candidate.SYSTEM_POLICY)

    def test_payload_is_deterministic_and_tool_free(self):
        left = candidate.build_payload("Turn on the kitchen light")
        self.assertEqual(left, candidate.build_payload("Turn on the kitchen light"))
        value = json.loads(left)
        self.assertNotIn("tools", value)
        self.assertEqual(0, value["temperature"])
        self.assertFalse(value["stream"])


if __name__ == "__main__":
    unittest.main()
