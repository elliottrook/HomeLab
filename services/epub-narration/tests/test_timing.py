from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.timing import SentenceCue, SentenceSpan, build_sentence_cues, validate_cues


class TimingTests(unittest.TestCase):
    def test_uses_exact_rendered_sample_lengths(self):
        spans = (
            SentenceSpan(0, 19, "Synthetic sentence."),
            SentenceSpan(20, 36, "Another fixture."),
        )
        cues = build_sentence_cues(spans, (24_000, 12_000), (2_400, 0))
        self.assertEqual((0, 24_000), (cues[0].start_sample, cues[0].end_sample))
        self.assertEqual((26_400, 38_400), (cues[1].start_sample, cues[1].end_sample))
        validate_cues(cues, 38_400)

    def test_rejects_zero_length_render_and_overlap(self):
        spans = (SentenceSpan(0, 5, "Words."),)
        with self.assertRaisesRegex(ValueError, "sentence-render-samples"):
            build_sentence_cues(spans, (0,), (0,))
        invalid = (
            SentenceCue(0, 5, 0, 100, "a" * 64),
            SentenceCue(6, 10, 90, 120, "b" * 64),
        )
        with self.assertRaisesRegex(ValueError, "sentence-time-order"):
            validate_cues(invalid, 120)


if __name__ == "__main__":
    unittest.main()

