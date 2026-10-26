import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).parent
SCRIPT = ROOT / "install_nlu_calibration_score_boundary.sh"


class ScoreBoundaryInstallTests(unittest.TestCase):
    def test_transaction_is_exact_inactive_and_recoverable(self):
        source = SCRIPT.read_text()
        self.assertIn("source_commit=9f4da72d", source)
        self.assertIn("old_score=ec4f4e44ff595617f1fe8e337b587bbab049204d001dd2ba050ee1fb146022fd", source)
        self.assertIn("new_score=7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd", source)
        self.assertIn("old_journal=992960fe76540941fe9adf7b75ddaf82541c55039782bf4cf360ad6c5279a744", source)
        self.assertIn("new_journal=966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb", source)
        self.assertIn("trap rollback ERR", source)
        self.assertIn("$checkpoint/$name", source)
        self.assertIn("--staged-directory \"$target\"", source)
        self.assertIn("test_root=/tmp/nlu-score-tests-$source_commit", source)
        self.assertIn("$test_root/fixtures/nlu-development-v1.json", source)
        self.assertIn("cd '$test_root'", source)
        self.assertNotIn("check_installed nlu_calibration_stage_manifest.py", source)
        self.assertNotIn("check_installed nlu-calibration-stage-manifest-v1.json", source)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", source)
        self.assertNotIn("systemctl start", source)
        self.assertNotIn("systemctl stop", source)
        self.assertNotIn("local-ai-lease acquire", source)
        self.assertNotIn("/v1/chat/completions", source)
        self.assertNotIn("rm -rf", source)

    def test_pinned_local_inputs_match(self):
        expected = {
            "nlu_calibration_score.py": "7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd",
            "nlu_calibration_journal.py": "966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb",
            "nlu_calibration_stage_manifest.py": "83c7ed1135e444d832518e95bc7df51c59d5cb1c3cc7041177f31fc8cb84c3c9",
            "fixtures/nlu-calibration-stage-manifest-v1.json": "7b547d9b38d3be1d951e2d8cbeee011a723f8582006c0885ad37d01f5388ee80",
            "test_nlu_calibration_score.py": "b6d86d82eb6e272a159c1f65b7ae78824a445576fdb26a43ac8990ca7dcef3b0",
            "test_nlu_calibration_corpus.py": "3147b69314866239ae8d2ce61b8e7d1e98121d9d5bc96548d154aef5f20ba8c0",
        }
        for relative, digest in expected.items():
            with self.subTest(path=relative):
                self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
