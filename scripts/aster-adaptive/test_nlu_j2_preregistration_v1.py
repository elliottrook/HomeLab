import copy
import json
from pathlib import Path
import unittest

import nlu_j2_preregistration_v1 as prereg


MANIFEST = Path(__file__).parent / "fixtures" / "nlu-j2-preregistration-v1.json"


class J2PreregistrationTests(unittest.TestCase):
    def test_exact_manifest_is_source_only_and_non_authorizing(self):
        result = prereg.validate(MANIFEST.read_bytes())
        self.assertEqual("not-created", result["corpus_status"])
        self.assertEqual("not-created", result["evaluation_status"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_duplicate_keys_fail_closed(self):
        with self.assertRaises(ValueError):
            prereg.validate(b'{"schema":"one","schema":"two"}')

    def test_architecture_drift_fails_closed(self):
        value = json.loads(MANIFEST.read_text())
        value["architecture"]["pretrained_weights"] = True
        with self.assertRaisesRegex(ValueError, "architecture"):
            prereg.validate(prereg.canonical(value))

    def test_evaluation_cannot_be_unsealed_or_retried(self):
        for field, changed in (("sealed_before_training", False), ("retries", 1)):
            value = json.loads(MANIFEST.read_text())
            value["evaluation"][field] = changed
            with self.assertRaisesRegex(ValueError, "evaluation"):
                prereg.validate(prereg.canonical(value))

    def test_corpus_counts_and_roles_are_frozen(self):
        for field, changed in (("total_train", 767),
                               ("generator_role", "trainer"),
                               ("normalized_overlap_required", 1)):
            value = json.loads(MANIFEST.read_text())
            value["corpus"][field] = changed
            with self.assertRaisesRegex(ValueError, "corpus"):
                prereg.validate(prereg.canonical(value))

    def test_j1_failure_or_artifact_identity_cannot_enter_manifest(self):
        for digest in (prereg.EXPOSED_J1_RESULT_SHA256,
                       prereg.FORBIDDEN_J1_ARTIFACT_SHA256):
            value = json.loads(MANIFEST.read_text())
            value["prohibitions"].append(digest)
            with self.assertRaises(ValueError):
                prereg.validate(prereg.canonical(value))

    def test_runtime_cannot_gain_effects(self):
        value = json.loads(MANIFEST.read_text())
        value["runtime_boundary"]["route_effects"] = "allowed"
        with self.assertRaisesRegex(ValueError, "runtime"):
            prereg.validate(prereg.canonical(value))


if __name__ == "__main__":
    unittest.main()
