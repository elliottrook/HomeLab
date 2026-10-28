import sys
import types
import unittest
from unittest.mock import patch

import youtube_back


class YouTubeBackTests(unittest.TestCase):
    def test_root_returns_to_home(self):
        self.assertEqual(youtube_back.action_for(youtube_back.ROOT),
                         ("Action(Back)",))

    def test_search_returns_to_owned_root_then_focuses_first_row(self):
        actions = youtube_back.action_for(
            youtube_back.ROOT + "kodion/search/query/?q=OpenAI")
        self.assertEqual(actions[0],
                         "Container.Update(plugin://plugin.video.youtube/,replace)")
        self.assertIn("SetFocus(9530)", actions[1])

    def test_other_window_preserves_normal_back(self):
        self.assertEqual(youtube_back.action_for("plugin://plugin.video.plex/"),
                         ("Action(Back)",))

    def test_main_executes_only_classified_actions(self):
        called = []
        xbmc = types.SimpleNamespace(
            getInfoLabel=lambda _: youtube_back.ROOT + "special/subscriptions/",
            executebuiltin=called.append,
        )
        with patch.dict(sys.modules, {"xbmc": xbmc}):
            youtube_back.main()
        self.assertEqual(called, list(youtube_back.action_for(
            youtube_back.ROOT + "special/subscriptions/")))


if __name__ == "__main__":
    unittest.main()
