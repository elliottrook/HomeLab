import copy
import json
from pathlib import Path
import unittest

from epub_chapter import chapter
from epub_fixture import build_readalong
from word_group_narration import build


HERE = Path(__file__).parent
AUDIO = '1da10ad89f095d2c619cff92760564d701401c8a50261b40c98eda228d001466'


class WordGroupNarrationTests(unittest.TestCase):
    def setUp(self):
        self.book = chapter(build_readalong())
        self.fixture = json.loads((HERE/'fixtures/aster-epub-word-groups-synthetic.json').read_text())

    def test_fixture_covers_exact_source_with_measured_connected_phrases(self):
        plan = build(self.book, self.fixture, AUDIO)
        labels = [self.book.text[item.text_start:item.text_end] for item in plan.units]
        self.assertEqual((len(labels), plan.total_samples), (34, 252399))
        self.assertEqual(labels[9], 'From the')
        self.assertEqual(labels[32], 'of the')
        self.assertEqual(sum(len(label.split()) for label in labels), 36)
        self.assertIsNone(plan.active(0, AUDIO))
        self.assertEqual(plan.active(plan.units[0].sample_start, AUDIO), plan.units[0])
        self.assertIsNone(plan.active(plan.units[-1].sample_end, AUDIO))

    def test_identity_counts_spans_and_samples_are_fail_closed(self):
        changes = (
            ('source_sha256', '0'*64),
            ('audio_sha256', '0'*64),
            ('source_word_count', 35),
            ('spoken_group_count', 33),
        )
        for name, value in changes:
            fixture = copy.deepcopy(self.fixture); fixture[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                build(self.book, fixture, AUDIO)
        for field, value in (('start_character', 1), ('end_character', 3),
                             ('start_sample', -1), ('end_sample', 999999)):
            fixture = copy.deepcopy(self.fixture); fixture['cues'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build(self.book, fixture, AUDIO)

    def test_schema_drift_is_refused(self):
        fixture = copy.deepcopy(self.fixture); fixture['unknown'] = True
        with self.assertRaisesRegex(ValueError, 'word-group-fixture-schema'):
            build(self.book, fixture, AUDIO)


if __name__ == '__main__':
    unittest.main()
