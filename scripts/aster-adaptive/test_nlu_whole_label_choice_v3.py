from __future__ import annotations

import json
import unittest

import nlu_whole_label_choice_v2 as v2
import nlu_whole_label_choice_v3 as v3


class WholeLabelChoiceV3Tests(unittest.TestCase):
    def test_final_revision_changes_only_public_rubric(self):
        self.assertIs(v2.CATALOGUE, v3.CATALOGUE)
        self.assertIs(v2.RESPONSE_SCHEMA, v3.RESPONSE_SCHEMA)
        self.assertIs(v2.interpret, v3.interpret)
        self.assertNotEqual(v2.SYSTEM_POLICY, v3.SYSTEM_POLICY)
        self.assertIn("conversational words such as me", v3.RUBRIC)
        self.assertIn("use change-request when the verb is fix", v3.RUBRIC)

    def test_payload_remains_bounded_selection(self):
        payload = json.loads(v3.build_payload("Fix it"))
        self.assertEqual({"label_id"}, set(payload["response_format"]["schema"]["properties"]))
        self.assertNotIn("tools", payload)
        self.assertEqual(v3.MODEL, payload["model"])


if __name__ == "__main__":
    unittest.main()
