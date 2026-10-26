import unittest
import numbers

from word_alignment import TimedWord, align_exact


class WordAlignmentTests(unittest.TestCase):
    class RealScalar(numbers.Real):
        def __init__(self, value): self.value = value
        def __float__(self): return float(self.value)
        def __trunc__(self): return int(self.value)
        def __floor__(self): return int(self.value)
        def __ceil__(self): return int(self.value)
        def __round__(self, ndigits=None): return round(self.value, ndigits) if ndigits is not None else round(self.value)
        def __abs__(self): return type(self)(abs(self.value))
        def __neg__(self): return type(self)(-self.value)
        def __pos__(self): return self
        def __add__(self, other): return self.value + other
        __radd__ = __add__
        def __sub__(self, other): return self.value - other
        def __rsub__(self, other): return other - self.value
        def __mul__(self, other): return self.value * other
        __rmul__ = __mul__
        def __truediv__(self, other): return self.value / other
        def __rtruediv__(self, other): return other / self.value
        def __floordiv__(self, other): return self.value // other
        def __rfloordiv__(self, other): return other // self.value
        def __mod__(self, other): return self.value % other
        def __rmod__(self, other): return other % self.value
        def __pow__(self, other): return self.value ** other
        def __rpow__(self, other): return other ** self.value
        def __eq__(self, other): return self.value == other
        def __lt__(self, other): return self.value < other
        def __le__(self, other): return self.value <= other
        def __hash__(self): return hash(self.value)

    def test_exact_measured_words_bind_to_source_characters(self):
        source = "Mara couldn't wait; the rain had begun."
        words = (
            TimedWord(" Mara", .12, .42), TimedWord("couldn't", .44, .91),
            TimedWord(" wait,", .93, 1.22), TimedWord("the", 1.31, 1.48),
            TimedWord(" rain", 1.50, 1.82), TimedWord("had", 1.84, 2.01),
            TimedWord("begun.", 2.03, 2.42),
        )
        cues = align_exact(source, words, 2.8)
        self.assertEqual([source[c.start_character:c.end_character] for c in cues],
                         ["Mara", "couldn't", "wait", "the", "rain", "had", "begun"])
        self.assertEqual((cues[0].start_seconds, cues[-1].end_seconds), (.12, 2.42))

    def test_unicode_case_and_curly_apostrophe_are_lossless(self):
        source = "Été Mara’s"
        cues = align_exact(source, (TimedWord("été", 0, .3), TimedWord("MARA'S", .4, .8)), 1)
        self.assertEqual([source[c.start_character:c.end_character] for c in cues], ["Été", "Mara’s"])

    def test_real_number_scalar_timings_are_accepted_but_booleans_are_not(self):
        scalar = self.RealScalar
        cues = align_exact("one", (TimedWord("one", scalar(.1), scalar(.4)),), scalar(1))
        self.assertEqual((cues[0].start_seconds, cues[0].end_seconds), (.1, .4))
        for start, end, duration in ((True, .4, 1), (.1, False, 1), (.1, .4, True)):
            with self.assertRaises(ValueError):
                align_exact("one", (TimedWord("one", start, end),), duration)

    def test_substitution_insertion_omission_and_multiword_token_refused(self):
        source = "one quiet room"
        invalid = (
            (TimedWord("one", 0, .1), TimedWord("noisy", .2, .3), TimedWord("room", .4, .5)),
            (TimedWord("one", 0, .1), TimedWord("quiet", .2, .3)),
            (TimedWord("one", 0, .1), TimedWord("extra", .2, .3),
             TimedWord("quiet", .4, .5), TimedWord("room", .6, .7)),
            (TimedWord("one quiet", 0, .2), TimedWord("quiet", .3, .4), TimedWord("room", .5, .6)),
        )
        for words in invalid:
            with self.subTest(words=words), self.assertRaises(ValueError):
                align_exact(source, words, 1)

    def test_unmeasured_or_impossible_time_is_never_interpolated(self):
        for words, duration in (
            ((TimedWord("one", -.1, .2),), 1),
            ((TimedWord("one", .2, .2),), 1),
            ((TimedWord("one", .3, .2),), 1),
            ((TimedWord("one", .2, 1.1),), 1),
            ((TimedWord("one", float("nan"), .2),), 1),
        ):
            with self.subTest(words=words), self.assertRaises(ValueError):
                align_exact("one", words, duration)

    def test_overlap_wrong_type_empty_and_bounds_refused(self):
        with self.assertRaises(ValueError):
            align_exact("one two", (TimedWord("one", 0, .4), TimedWord("two", .3, .6)), 1)
        for source, words, duration in (("", (), 1), ("one", (object(),), 1),
                                        ("one", (TimedWord("one", 0, .1),), 0)):
            with self.subTest(source=source), self.assertRaises(ValueError):
                align_exact(source, words, duration)


if __name__ == "__main__":
    unittest.main()
