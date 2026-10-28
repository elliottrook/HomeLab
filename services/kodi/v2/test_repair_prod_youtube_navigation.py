import json
from pathlib import Path
import tempfile
import unittest

from tools.repair_prod_youtube_navigation import BACK_ACTION, candidates, sha


class ProductionYouTubeNavigationRepairTests(unittest.TestCase):
    def test_candidate_preserves_dedicated_rows_and_scopes_back(self):
        home = (b'<window><controls><control id="136"><onclick>ActivateWindow('
                b'Videos,&quot;plugin://plugin.video.youtube/&quot;,return)</onclick>'
                b'</control></controls></window>')
        nav = (b'<window><controls><control id="9530"/><control id="9531"/>'
               b'<control id="9532"/><control id="9305"><onclick>Action(Back)'
               b'</onclick></control><control id="9404"><onclick>Action(Back)'
               b'</onclick></control></controls></window>')
        keymap = b'<keymap><global /></keymap>'
        family = json.dumps({"skin": {"1080i/Home.xml": sha(home)}}).encode()
        after = candidates(home, nav, keymap, family, b'helper')
        self.assertEqual(home, after[0])
        self.assertEqual(after[1].count(BACK_ACTION.encode()), 2)
        self.assertEqual(after[2].count(BACK_ACTION.encode()), 4)
        self.assertEqual(json.loads(after[3])["skin"]["tools/youtube_back.py"],
                         sha(b'helper'))


if __name__ == "__main__":
    unittest.main()
