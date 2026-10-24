import tempfile,unittest
from music_entry import parse_entry,entry_lock


class EntryTests(unittest.TestCase):
    def test_only_exact_id_only_routes_are_accepted(self):
        self.assertEqual(parse_entry([]),('pilot',None))
        self.assertEqual(parse_entry(['genres']),('genres',None))
        self.assertEqual(parse_entry(['shuffle']),('shuffle',None))
        self.assertEqual(parse_entry(['album','12']),('album',12))
        self.assertEqual(parse_entry(['song','13']),('song',13))
        self.assertEqual(parse_entry(['playlist','1'*32]),('playlist','1'*32))
        for args in (['url','https://private.invalid'],['album','0'],['song','-1'],
                     ['song','１'],['song','2147483648'],['album','12),PlayMedia(x)'],
                     ['playlist','not-an-id'],['shuffle','1'],['genres','extra'],['album']):
            with self.assertRaises(ValueError):parse_entry(args)

    def test_admission_refuses_duplicate_and_releases_after_exit_or_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with entry_lock(directory):
                with self.assertRaisesRegex(ValueError,'already-open'):
                    with entry_lock(directory):pass
            with self.assertRaises(RuntimeError):
                with entry_lock(directory):raise RuntimeError('simulated-exit')
            with entry_lock(directory):pass
