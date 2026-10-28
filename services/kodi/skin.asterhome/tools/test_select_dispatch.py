import unittest

from select_dispatch import dispatched_action


class SelectDispatchTests(unittest.TestCase):
    def test_music_tiles_open_the_selected_item(self):
        self.assertEqual(
            dispatched_action(11114, 500),
            'RunScript(special://skin/tools/music_data.py,albums,open)',
        )

    def test_books_home_rows_activate(self):
        self.assertEqual(
            dispatched_action(11110, 502),
            'RunScript(special://skin/tools/books_data.py,home,activate)',
        )

    def test_non_list_controls_keep_native_select(self):
        self.assertIsNone(dispatched_action(11114, 110))
        self.assertIsNone(dispatched_action(10025, 50))

    def test_search_catalogue_uses_explicit_script_route(self):
        self.assertEqual(
            dispatched_action(11127, 51),
            'RunScript(script.asterseerr)',
        )

    def test_digest_story_and_player_track_activate(self):
        self.assertEqual(
            dispatched_action(11111, 500),
            'RunScript(special://skin/tools/hub_data.py,digest,chapter)',
        )
        self.assertEqual(
            dispatched_action(11121, 50),
            'RunScript(special://skin/tools/music_data.py,music-player,track)',
        )
        self.assertIsNone(dispatched_action(11121, 9000))


if __name__ == '__main__':
    unittest.main()
