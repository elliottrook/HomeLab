from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("nlu_k2_apple_embedding_shortlister_v1.swift")


class K2AppleEmbeddingShortlisterSourceTests(unittest.TestCase):
    def test_source_has_fixed_shape_and_create_only_output(self):
        text = SOURCE.read_text()
        for required in (
            "corpus.cases.count == 960",
            "train.count == 768",
            "validation.count == 192",
            "labels.count == 16",
            "embedding.dimension == 300",
            "shortlist = Array(scores.prefix(4))",
            "options: [.withoutOverwriting]",
            "lstat(path, &info)",
            "chmod(outputPath, S_IRUSR | S_IWUSR)",
        ):
            self.assertIn(required, text)

    def test_source_does_not_embed_private_paths_or_model_transport(self):
        text = SOURCE.read_text()
        for forbidden in (
            "/Users/jelliott/lab/private-benchmarks",
            "192.168.",
            "http://",
            "https://",
            "sealed-evaluation",
            "URLSession",
        ):
            self.assertNotIn(forbidden, text)

    def test_stdout_summary_does_not_include_rows_or_text(self):
        text = SOURCE.read_text()
        summary_block = text.split('let summary: [String: Any] = [', 1)[1]
        self.assertNotIn('"rows"', summary_block)
        self.assertNotIn('row.text', summary_block)


if __name__ == "__main__":
    unittest.main()
