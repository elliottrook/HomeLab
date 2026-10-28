import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "repair_search_catalogue", HERE / "tools/repair_search_catalogue.py")
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)


class SearchCatalogueRepairTests(unittest.TestCase):
    def test_adds_explicit_route_and_centres_both_pills(self):
        select = (b"def dispatched_action(window_id, focus_id):\n"
                  b"    if window_id in MUSIC_WINDOWS and focus_id == 500:\n"
                  b"        return 'music'\n")
        common = (b'<texturenofocus border="20" colordiffuse="cc202b25">'
                  b'special://skin/media/ui-panel.png</texturenofocus>')
        search = (b'<control type="button" id="50">' + common
                  + b'<onclick>SetFocus(10)</onclick></control>'
                  + b'<control type="button" id="51">' + common
                  + b'<onclick>RunScript(script.asterseerr)</onclick></control>')
        select_after, search_after = REPAIR.candidates(select, search)
        self.assertIn(b"window_id == 11127 and focus_id == 51", select_after)
        self.assertEqual(search_after.count(
            b'<align>center</align><aligny>center</aligny>'), 2)
        self.assertEqual(search_after.count(b'RunScript(script.asterseerr)'), 1)


if __name__ == "__main__":
    unittest.main()
