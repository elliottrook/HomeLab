import unittest
from unittest.mock import Mock

from books_player import focus_first_entry, is_books_parent


class BooksPlayerTests(unittest.TestCase):
    def test_only_books_parent_is_redirected(self):
        self.assertTrue(is_books_parent('plugin://plugin.audio.asterbooks/?action=book', '..'))
        self.assertFalse(is_books_parent('plugin://plugin.audio.asterbooks/?action=book', 'Chapter 1'))
        self.assertFalse(is_books_parent('musicdb://albums/', '..'))

    def test_waits_for_directory_then_skips_parent(self):
        xbmc, gui = Mock(), Mock()
        gui.getCurrentWindowId.return_value = 10502
        counts = iter(['0', '37'])
        xbmc.getInfoLabel.side_effect = lambda key: (
            'plugin://plugin.audio.asterbooks/?action=book' if key == 'Container.FolderPath'
            else next(counts) if key.endswith('NumItems') else '..')
        xbmc.Monitor.return_value.waitForAbort.return_value = False
        window = gui.Window.return_value
        window.getFocusId.return_value = 50
        focus_first_entry(xbmc, gui)
        xbmc.executebuiltin.assert_called_once_with('SetFocus(50,1,absolute)')

    def test_does_not_move_an_existing_chapter_selection(self):
        xbmc, gui = Mock(), Mock()
        gui.getCurrentWindowId.return_value = 10502
        xbmc.getInfoLabel.side_effect = lambda key: (
            'plugin://plugin.audio.asterbooks/?action=episodes' if key == 'Container.FolderPath'
            else '8' if key.endswith('NumItems') else 'Chapter 3')
        window = gui.Window.return_value
        window.getFocusId.return_value = 50
        focus_first_entry(xbmc, gui)
        xbmc.executebuiltin.assert_not_called()
