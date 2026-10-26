import copy
import json
from pathlib import Path
import tempfile
import unittest

from validate_d4_candidate_h_bundle import MANIFEST, ROOT, validate


class D4CandidateHBundleTests(unittest.TestCase):
    def test_frozen_bundle_validates(self):
        self.assertEqual(
            validate(),
            {
                "candidate": "d4-candidate-h-unprivileged-v1",
                "packet_files": 11,
                "control_files": 3,
                "validation_files": 1,
                "activation": "inactive-source-only",
            },
        )

    def test_rejects_identity_or_activation_expansion(self):
        data = json.loads(MANIFEST.read_text())
        for mutation in (
            lambda value: value["identity"]["supplementary_groups"].append("aster"),
            lambda value: value.update(activation="active"),
        ):
            changed = copy.deepcopy(data)
            mutation(changed)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    validate(path, ROOT)

    def test_rejects_control_hash_or_model_call_expansion(self):
        data = json.loads(MANIFEST.read_text())
        for mutation in (
            lambda value: value["control_files"][0].update(source_sha256="0" * 64),
            lambda value: value["excluded"].remove("model-call"),
        ):
            changed = copy.deepcopy(data)
            mutation(changed)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    validate(path, ROOT)


if __name__ == "__main__":
    unittest.main()
