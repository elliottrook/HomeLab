import unittest

from music_queue import QueueSnapshot, nonholiday_shuffle, propose


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.current = QueueSnapshot((10, 20, 10, 30), 1)

    def test_next_preserves_current_and_existing_duplicate_order(self):
        plan = propose(self.current, [70, 80], action='next')
        self.assertEqual(plan.song_ids, (10, 20, 70, 80, 10, 30))
        self.assertEqual(plan.current_index, 1)
        self.assertFalse(plan.replaces_queue)

    def test_append_does_not_change_current_position(self):
        plan = propose(self.current, [70], action='append')
        self.assertEqual(plan.song_ids, (10, 20, 10, 30, 70))
        self.assertEqual(plan.current_index, 1)

    def test_replace_is_explicit_without_an_automatic_start_position(self):
        plan = propose(self.current, [80, 70], action='replace')
        self.assertEqual(plan.song_ids, (80, 70))
        self.assertTrue(plan.replaces_queue)
        self.assertIsNone(plan.current_index)

    def test_stale_preview_checks_queue_order_duplicates_and_current(self):
        plan = propose(self.current, [70], action='next')
        self.assertTrue(plan.matches(self.current))
        for other in (QueueSnapshot((10, 20, 30), 1),
                      QueueSnapshot((10, 10, 20, 30), 1),
                      QueueSnapshot(self.current.song_ids, 2)):
            self.assertFalse(plan.matches(other))

    def test_no_current_position_cannot_guess_play_next(self):
        with self.assertRaises(ValueError):
            propose(QueueSnapshot((10,), None), [20], action='next')
        self.assertEqual(propose(QueueSnapshot((), None), [20], action='append').song_ids, (20,))

    def test_invalid_identities_positions_actions_fail_closed(self):
        for ids in ([True], [0], [-1], ['20'], '20'):
            with self.assertRaises(ValueError): QueueSnapshot(ids, None)
            with self.assertRaises(ValueError): propose(self.current, ids, action='append')
        for index in (-1, 4, True, '1'):
            with self.assertRaises(ValueError): QueueSnapshot((10, 20, 10, 30), index)
        with self.assertRaises(ValueError): propose(self.current, [], action='replace')
        with self.assertRaises(ValueError): propose(self.current, [20], action='play')

    def test_inputs_are_owned_and_not_mutated(self):
        ids = [10, 20]; selected = [70]
        snapshot = QueueSnapshot(ids, 0)
        plan = propose(snapshot, selected, action='next')
        ids.append(30); selected.append(80)
        self.assertEqual(snapshot.song_ids, (10, 20))
        self.assertEqual(plan.song_ids, (10, 70, 20))

    def test_combined_queue_bound_is_checked(self):
        with self.assertRaises(ValueError):
            propose(QueueSnapshot((10,)*100000, 0), [20], action='append')

    def test_shuffle_excludes_direct_and_album_holiday_not_title(self):
        songs = [dict(songid=1, albumid=10, genre=['Rock'], label='Christmas title'),
                 dict(songid=2, albumid=20, genre=['Rock']),
                 dict(songid=3, albumid=10, genre=['Christmas']),
                 dict(songid=4, albumid=10, genre=['Rock'])]
        albums = [dict(albumid=10, genre=['Rock']), dict(albumid=20, genre=['Christmas'])]
        result = nonholiday_shuffle(songs, albums, expected_total=4, seed=42)
        self.assertEqual(set(result), {1, 4})
        self.assertEqual(result, nonholiday_shuffle(list(reversed(songs)), albums,
                                                 expected_total=4, seed=42))
        self.assertEqual([s['songid'] for s in songs], [1, 2, 3, 4])
        with self.assertRaises(ValueError):
            nonholiday_shuffle(songs, albums, expected_total=5, seed=42)

    def test_empty_holiday_pool_is_truthful_and_cannot_replace_queue(self):
        result = nonholiday_shuffle([dict(songid=1, genre=['Christmas'])], [],
                                   expected_total=1, seed=0)
        self.assertEqual(result, ())
        with self.assertRaises(ValueError): propose(self.current, result, action='replace')


if __name__ == '__main__': unittest.main()
