"""A retained snapshot must hold candidates before a deletion is planned."""

import tempfile
from pathlib import Path
from unittest import TestCase

from video_archiver.retention_reclaim import estimate_unprotected_file


class ReclaimTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Media' / 'data'
        self.file = self.root / 'archive-movies' / 'a.mkv'
        self.file.parent.mkdir(parents=True)
        self.file.write_bytes(b'video')

    def test_file_not_in_snapshot_has_optimistic_estimate(self):
        result = estimate_unprotected_file(self.file, data_root=self.root,
                                           snapshots=('older',))
        self.assertEqual(result.bytes, 5)

    def test_file_in_any_snapshot_is_held(self):
        archived = self.root / '.zfs' / 'snapshot' / 'newer' / 'archive-movies' / 'a.mkv'
        archived.parent.mkdir(parents=True)
        archived.write_bytes(b'video')
        result = estimate_unprotected_file(self.file, data_root=self.root,
                                           snapshots=('older', 'newer'))
        self.assertEqual(result.bytes, 0)
        self.assertEqual(result.reason, 'file retained by snapshot')

    def test_escape_and_invalid_snapshot_names_hold(self):
        outside = Path(self.temp.name) / 'outside.mkv'
        outside.write_bytes(b'video')
        self.assertEqual(estimate_unprotected_file(outside, data_root=self.root,
                                                   snapshots=()).bytes, 0)
        self.assertEqual(estimate_unprotected_file(self.file, data_root=self.root,
                                                   snapshots=('../escape',)).bytes, 0)
