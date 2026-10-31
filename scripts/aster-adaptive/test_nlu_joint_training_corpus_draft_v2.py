import json
import unittest
from pathlib import Path

import nlu_joint_training_corpus_draft_v2 as draft
import nlu_joint_training_corpus_v1 as boundary
import nlu_joint_training_naturalness_v1 as naturalness
import nlu_whole_label_choice_v1 as ontology


FIXTURES = Path(__file__).with_name("fixtures")
SOURCE = FIXTURES / "nlu-j1-training-draft-v2.json"
PUBLIC = FIXTURES / "nlu-development-v1.json"


class J1CorpusDraftV2Tests(unittest.TestCase):
    def test_generator_reproduces_frozen_candidate(self):
        self.assertEqual(SOURCE.read_bytes(), draft.canonical(draft.build()))

    def test_candidate_is_balanced_and_public_disjoint(self):
        summary = boundary.validate_corpus(
            SOURCE.read_bytes(), {"development-v1": PUBLIC.read_bytes()}
        )
        self.assertEqual(400, summary["case_count"])
        self.assertEqual(320, summary["train_count"])
        self.assertEqual(80, summary["validation_count"])
        self.assertEqual(0, summary["overlap_count"])

    def test_candidate_passes_deterministic_naturalness_gate(self):
        summary = naturalness.validate(SOURCE.read_bytes())
        self.assertEqual("pass", summary["deterministic_naturalness_gate"])
        self.assertGreaterEqual(summary["unique_four_token_prefixes"], 390)
        self.assertLessEqual(summary["max_four_token_prefix_reuse"], 4)

    def test_v1_cartesian_draft_fails_new_naturalness_gate(self):
        old = FIXTURES / "nlu-j1-training-draft-v1.json"
        with self.assertRaises(ValueError):
            naturalness.validate(old.read_bytes())

    def test_candidate_metadata_remains_non_authoritative(self):
        value = json.loads(SOURCE.read_text())
        self.assertEqual("synthetic", value["data_class"])
        self.assertEqual("not-granted", value["authority"])

    def test_every_label_survives_the_actual_interpreter_unchanged(self):
        value = json.loads(SOURCE.read_text())
        for case in value["cases"]:
            response = json.dumps({
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"label_id": case["label_id"]}),
                    },
                    "finish_reason": "stop",
                }]
            }, sort_keys=True, separators=(",", ":")).encode()
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    ontology.CATALOGUE[case["label_id"]],
                    ontology.interpret(case["text"], response),
                )


if __name__ == "__main__":
    unittest.main()
