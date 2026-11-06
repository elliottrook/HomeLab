import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


PATH = Path(__file__).with_name("measure_artwork_readiness.py")
SPEC = importlib.util.spec_from_file_location("measure_artwork_readiness", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ArtworkReadinessTests(unittest.TestCase):
    def test_scope_is_content_free_and_covers_core_art_pages(self):
        source = PATH.read_text()
        self.assertEqual([row[0] for row in MODULE.ROUTES],
                         ["media", "books", "news", "music", "youtube"])
        self.assertIn('rpc("XBMC.GetInfoBooleans"', source)
        self.assertIn('action("ActivateWindow(Home)")', source)
        for forbidden in ("GetInfoLabels", "Player.Open", "Player.Stop",
                          "Player.GetItem", "Files.GetDirectory", "VideoLibrary",
                          "AudioLibrary", "screenshot", "Texture13.db"):
            self.assertNotIn(forbidden, source)

    def test_boolean_count_rejects_shape_drift(self):
        expressions = ("a", "b")
        with patch.object(MODULE, "rpc", return_value={"a": True, "b": False}):
            self.assertEqual(MODULE.booleans(expressions), 1)
        with patch.object(MODULE, "rpc", return_value={"a": True}):
            with self.assertRaisesRegex(RuntimeError, "art-boolean-format"):
                MODULE.booleans(expressions)

    def test_art_binding_must_remain_stable(self):
        ticks = iter(index / 10 for index in range(20))
        with patch.object(MODULE, "booleans", side_effect=[1, 0, 1, 1]), \
                patch.object(MODULE.time, "monotonic",
                             side_effect=lambda: next(ticks)), \
                patch.object(MODULE.time, "sleep"):
            ready, count = MODULE.wait_art(("art",), 1, timeout=1,
                                           stable_seconds=.15)
        self.assertEqual(ready, 1.0)
        self.assertEqual(count, 1)

    def test_target_and_pass_bounds_fail_closed(self):
        with patch.object(MODULE.os, "uname") as uname:
            uname.return_value.nodename = "wrong-host"
            with self.assertRaisesRegex(RuntimeError, "art-target"):
                MODULE.run(1)
        with self.assertRaisesRegex(RuntimeError, "art-passes"):
            MODULE.main(["--passes", "0"])


if __name__ == "__main__":
    unittest.main()
