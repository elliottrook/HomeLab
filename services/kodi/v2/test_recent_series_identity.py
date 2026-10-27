"""Tests for the exact Recently Added series-identity successor."""

import pathlib
import tempfile
import unittest
from unittest.mock import patch

import build_recent_series_identity as builder
import recent_series_identity as subject


class RecentSeriesIdentityTests(unittest.TestCase):
    RAW = b'''def add_item(item, row):\n    if row['kind'] == 'tvshow':\n        url = f"videodb://tvshows/titles/{row['id']}/"\n'''

    def test_exact_successor_adds_tvshow_dbid(self):
        with patch.object(subject, 'PREDECESSOR', subject.sha(self.RAW)):
            candidate = subject.render(self.RAW)
        self.assertIn(b"item.getVideoInfoTag().setDbId(row['id'])", candidate)
        self.assertEqual(candidate.count(b"setDbId(row['id'])"), 1)

    def test_builder_emits_one_bounded_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary) / 'source'; source.mkdir()
            (source / 'default.py').write_bytes(self.RAW)
            output = pathlib.Path(temporary) / 'candidate'
            with patch.object(subject, 'PREDECESSOR', subject.sha(self.RAW)):
                pin = builder.build(source, output)
            self.assertEqual(len(pin), 64)
            self.assertTrue((output / 'payload' / builder.TARGET).is_file())


if __name__ == '__main__':
    unittest.main()
