from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name(
    "nlu_k2_apple_embedding_sealed_shortlister_v1.swift"
)


class K2AppleEmbeddingSealedShortlisterSourceTests(unittest.TestCase):
    def test_source_pins_exact_private_inputs_and_shape(self):
        text = SOURCE.read_text()
        for required in (
            'corpusSHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"',
            'evaluationSHA256 = "78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae"',
            "corpus.cases.count == 960",
            "train.count == 768",
            "evaluation.cases.count == 32",
            "evaluation.cases.filter({ $0.label_id == label }).count == 2",
            "embedding.dimension == 300",
            "let shortlist = Array(scores.prefix(4))",
        ):
            self.assertIn(required, text)

    def test_private_output_is_create_only_mode_0600_and_no_follow(self):
        text = SOURCE.read_text()
        for required in (
            "lstat(path, &info)",
            "info.st_nlink != 1",
            "O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW",
            "S_IRUSR | S_IWUSR",
            "fsync(descriptor)",
        ):
            self.assertIn(required, text)

    def test_stdout_summary_excludes_private_rows_scores_and_metrics(self):
        text = SOURCE.read_text()
        summary = text.split('let summary: [String: Any] = [', 1)[1]
        for forbidden in (
            '"rows"', '"shortlist_ids"', '"shortlist_scores"',
            "row.text", "row.label_id", "top_one", "top_four",
        ):
            self.assertNotIn(forbidden, summary)

    def test_source_has_no_network_or_private_absolute_path(self):
        text = SOURCE.read_text()
        for forbidden in (
            "URLSession", "http://", "https://", "192.168.",
            "/Users/", "/private/tmp/aster-j2-evaluation-custodian",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
