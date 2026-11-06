import hashlib
from pathlib import Path
import tempfile
import unittest

import stage_nlu_j2_training_inputs_v1 as stage


class StageJ2TrainingInputsTests(unittest.TestCase):
    def test_stage_is_exact_content_free_and_create_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "stage"
            receipt = stage.stage(output)
            self.assertTrue(receipt["content_free"])
            self.assertFalse(receipt["training_started"])
            self.assertEqual(stage.transaction.CORPUS_RELEASE_SHA256,
                             hashlib.sha256((output / "corpus-release.json").read_bytes()).hexdigest())
            self.assertEqual(stage.admission.validate_result(
                (output / "training-admission.json").read_bytes())[
                    "training_admission_sha256"],
                receipt["admission_file_sha256"])
            self.assertEqual({"corpus-release.json", "training-admission.json",
                              "stage-receipt.json"},
                             {path.name for path in output.iterdir()})
            self.assertTrue(all(path.stat().st_mode & 0o777 == 0o600
                                for path in output.iterdir()))
            with self.assertRaisesRegex(ValueError, "already exists"):
                stage.stage(output)


if __name__ == "__main__": unittest.main()
