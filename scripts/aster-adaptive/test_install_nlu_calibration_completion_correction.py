import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).parent
SCRIPT = ROOT / "install_nlu_calibration_completion_correction.sh"


class CompletionCorrectionInstallTests(unittest.TestCase):
    def test_transaction_is_exact_inactive_and_recoverable(self):
        source = SCRIPT.read_text()
        self.assertIn("source_commit=0e4b7311", source)
        self.assertIn(
            "old_runner=a8cca4daa3a0504b07e9dc70bee4d8e04d3f181ac742c53954718c6918fc5a0f",
            source,
        )
        self.assertIn(
            "new_runner=88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0",
            source,
        )
        self.assertIn("trap rollback ERR", source)
        self.assertIn("$checkpoint/nlu_calibration_runner.py", source)
        self.assertIn("--staged-directory \"$target\"", source)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", source)
        self.assertNotIn("systemctl start", source)
        self.assertNotIn("systemctl stop", source)
        self.assertNotIn("local-ai-lease acquire", source)
        self.assertNotIn("/v1/chat/completions", source)
        self.assertNotIn("rm -rf", source)

    def test_pinned_local_inputs_match(self):
        expected = {
            "nlu_calibration_runner.py": "88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0",
            "nlu_calibration_stage_manifest.py": "215e221165fafcacb43ccae7230c0cad13a6e19ca9e41ccab9e019f815dc42e5",
            "fixtures/nlu-calibration-stage-manifest-v1.json": "835bcb55ba93d25427b322c6cf93aee06cba1b5e7221af7fb63dbd41d1aab114",
            "test_nlu_calibration_runner.py": "c9bdc21bafd9bfcdc263c56addd12c29fa88a5bd3ef23ab4c85d04d18c3b555d",
        }
        for relative, digest in expected.items():
            with self.subTest(path=relative):
                self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
