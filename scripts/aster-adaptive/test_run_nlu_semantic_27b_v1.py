from pathlib import Path
import unittest


class Semantic27BCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = Path(__file__).with_name("run_nlu_semantic_27b_v1.sh").read_text()

    def test_exact_current_and_candidate_identities_are_pinned(self):
        self.assertIn("a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3", self.text)
        self.assertIn("0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5", self.text)
        self.assertIn("47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693", self.text)
        self.assertIn("Qwen3.8-27B-UD-IQ4_XS-00001-of-00002.gguf", self.text)

    def test_recovery_is_armed_before_first_stop(self):
        self.assertLess(
            self.text.index("trap restore EXIT HUP INT TERM"),
            self.text.rindex('pct exec "$guest" -- systemctl stop aster-llama.service'),
        )
        self.assertIn("systemctl start --no-block aster-llama.service", self.text)
        self.assertIn("test \"$attempt\" -lt 90 || status=1", self.text)

    def test_one_public_run_and_no_promotion(self):
        self.assertEqual(self.text.count("nlu_semantic_development_runner_v1.py"), 1)
        self.assertIn("--model aster-qwen3.8-27b", self.text)
        for forbidden in ("enable aster-b60", "disable aster-llama", "nlu-calibration", "nlu-holdout"):
            self.assertNotIn(forbidden, self.text)


if __name__ == "__main__":
    unittest.main()
