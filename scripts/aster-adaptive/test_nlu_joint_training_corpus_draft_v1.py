import json
import unittest
from pathlib import Path

import nlu_joint_training_corpus_draft_v1 as draft
import nlu_joint_training_corpus_v1 as boundary


FIXTURE = Path(__file__).with_name("fixtures") / "nlu-development-v1.json"


class J1DraftTests(unittest.TestCase):
    def test_draft_is_balanced_and_public_disjoint(self):
        value = draft.build()
        summary = boundary.validate_corpus(
            draft.canonical(value), {"development-v1": FIXTURE.read_bytes()})
        self.assertEqual(400, summary["case_count"])
        self.assertEqual(320, summary["train_count"])
        self.assertEqual(80, summary["validation_count"])
        self.assertEqual(0, summary["overlap_count"])

    def test_every_label_has_20_train_and_5_validation_cases(self):
        counts = {}
        for case in draft.build()["cases"]:
            key = (case["label_id"], case["split"])
            counts[key] = counts.get(key, 0) + 1
        for label_id in draft.LABELS.values():
            self.assertEqual(20, counts[(label_id, "train")])
            self.assertEqual(5, counts[(label_id, "validation")])

    def test_build_is_canonical_and_deterministic(self):
        first = draft.canonical(draft.build())
        second = draft.canonical(draft.build())
        self.assertEqual(first, second)
        value = json.loads(first)
        self.assertEqual(boundary.CUSTODIAN, value["custodian"])
        self.assertEqual("not-granted", value["authority"])


if __name__ == "__main__":
    unittest.main()
