import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pronunciation_lexicon import LexiconError, apply, load_corpus, load_lexicon
import verify_canonical_compatibility


HERE = Path(__file__).resolve().parent


class PronunciationLexiconTests(unittest.TestCase):
    def setUp(self):
        self.value, self.rules = load_lexicon(HERE / "pronunciation-lexicon-v1.json")
        self.cases = load_corpus(HERE / "retained-corpus-v1.json",
                                 lexicon_id=self.value["id"])

    def test_retained_corpus_and_idempotence(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                result = apply(case["input"], self.rules)
                self.assertEqual(result, case["expected"])
                self.assertEqual(apply(result, self.rules), result)

    def test_rule_ids_and_order_are_stable(self):
        self.assertEqual(
            [rule["id"] for rule, _ in self.rules],
            ["dotted-united-states", "dotted-british-columbia", "saint-petersburg",
             "emergency-nine-one-one", "lutron-caseta"],
        )

    def test_unknown_flag_and_duplicate_id_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lexicon.json"
            value = json.loads((HERE / "pronunciation-lexicon-v1.json").read_text())
            value["rules"][0]["flags"] = ["DOTALL"]
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(LexiconError, "LEXICON_RULE"):
                load_lexicon(path)
            value["rules"][0]["flags"] = ["IGNORECASE"]
            value["rules"][1]["id"] = value["rules"][0]["id"]
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(LexiconError, "LEXICON_RULE"):
                load_lexicon(path)

    def test_compatibility_verifier_requires_exact_canonical_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "canonical.py"
            path.write_text("def speech_text(value): return value\n")
            with mock.patch("sys.argv", ["verify", "--canonical", str(path)]):
                with self.assertRaisesRegex(SystemExit, "CANONICAL_DRIFT"):
                    verify_canonical_compatibility.main()


if __name__ == "__main__":
    unittest.main()
