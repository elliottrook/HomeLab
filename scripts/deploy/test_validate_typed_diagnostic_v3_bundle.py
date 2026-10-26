import json
import tempfile
import unittest
from pathlib import Path

from validate_typed_diagnostic_v3_bundle import MANIFEST, validate


class TypedDiagnosticV3BundleTests(unittest.TestCase):
    def candidate(self):
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def check_rejected(self, mutator):
        value = self.candidate()
        mutator(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate(path)

    def test_frozen_manifest_passes(self):
        validate()

    def test_candidate_drift_rejected(self):
        self.check_rejected(lambda value: value["files"][0].update(candidate_sha256="0" * 64))

    def test_target_or_rollback_broadening_rejected(self):
        for change in (
            lambda value: value["files"][0].update(target="/tmp/other"),
            lambda value: value["files"][2].update(rollback="retain"),
        ):
            with self.subTest(change=change):
                self.check_rejected(change)

    def test_missing_exclusion_or_duplicate_target_rejected(self):
        self.check_rejected(lambda value: value["exclusions"].remove("model_call"))
        self.check_rejected(lambda value: value["files"][2].update(target=value["files"][1]["target"]))


if __name__ == "__main__":
    unittest.main()
