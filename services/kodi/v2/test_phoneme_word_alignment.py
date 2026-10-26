import unittest

from phoneme_word_alignment import TimedPhoneme, align_phonemes


def timed(value, step=.1):
    return tuple(TimedPhoneme(char, index * step, (index + 1) * step)
                 for index, char in enumerate(value))


class PhonemeWordAlignmentTests(unittest.TestCase):
    def test_exact_phoneme_groups_bind_to_source_words(self):
        source = "Mara's rain fell."
        plan = "mˈɑːɹəz ɹˈeɪn fˈɛl."
        cues = align_phonemes(source, plan, timed(plan), len(plan) / 10 + .1)
        self.assertEqual([source[c.start_character:c.end_character] for c in cues],
                         ["Mara's", "rain", "fell"])
        self.assertEqual(cues[0].start_seconds, 0)
        self.assertAlmostEqual(cues[-1].end_seconds, len(plan) / 10)

    def test_source_punctuation_without_phoneme_word_boundary_is_refused(self):
        source = "Wait—then go."
        plan = "wˈeɪt—ðˈɛn ɡˈoʊ."
        with self.assertRaisesRegex(ValueError, "phoneme-alignment-word-count"):
            align_phonemes(source, plan, timed(plan), 2)

    def test_unknown_expansion_or_missing_word_is_refused(self):
        for source, plan in (("Room 2026", "ɹˈuːm twˈɛnti twˈɛnti sˈɪks"),
                             ("one two", "wˈʌn")):
            with self.subTest(source=source), self.assertRaisesRegex(
                    ValueError, "phoneme-alignment-word-count"):
                align_phonemes(source, plan, timed(plan), 4)

    def test_sequence_drift_and_punctuation_only_group_are_refused(self):
        plan = "wˈʌn tˈuː"
        changed = list(timed(plan)); changed[0] = TimedPhoneme("x", 0, .1)
        with self.assertRaisesRegex(ValueError, "phoneme-alignment-sequence"):
            align_phonemes("one two", plan, changed, 2)
        punctuation = ". wˈʌn"
        with self.assertRaisesRegex(ValueError, "phoneme-alignment-unspoken-word"):
            align_phonemes("one two", punctuation, timed(punctuation), 2)

    def test_zero_overlap_nonfinite_and_out_of_duration_are_refused(self):
        plan = "wˈʌn"
        cases = (
            (TimedPhoneme("w", 0, 0), *timed(plan[1:])),
            (TimedPhoneme("w", 0, .2), TimedPhoneme("ˈ", .1, .3),
             TimedPhoneme("ʌ", .3, .4), TimedPhoneme("n", .4, .5)),
            (TimedPhoneme("w", 0, float("nan")), *timed(plan[1:])),
            tuple(TimedPhoneme(char, i, i + 1) for i, char in enumerate(plan)),
        )
        for values in cases:
            with self.subTest(values=values), self.assertRaises(ValueError):
                align_phonemes("one", plan, values, .9)

    def test_boundaries_types_and_counts_are_refused(self):
        for source, plan, values, duration in (
            ("one", " wˈʌn", timed(" wˈʌn"), 2),
            ("one", "wˈʌn ", timed("wˈʌn "), 2),
            ("one two", "wˈʌn  tˈuː", timed("wˈʌn  tˈuː"), 2),
            ("one", "wˈʌn", timed("wˈʌ"), 2),
            ("one", "wˈʌn", (object(),) * 4, 2),
            ("one", "wˈʌn", timed("wˈʌn"), True),
        ):
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                align_phonemes(source, plan, values, duration)


if __name__ == "__main__":
    unittest.main()
