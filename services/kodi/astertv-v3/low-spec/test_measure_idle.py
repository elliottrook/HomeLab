import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


PATH = Path(__file__).with_name("measure_idle.py")
SPEC = importlib.util.spec_from_file_location("measure_idle", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IdleMeasurementTests(unittest.TestCase):
    def test_cpu_and_memory_parsers_are_bounded(self):
        self.assertEqual(MODULE.cpu_counts("cpu  10 2 3 80 5 0 0 0\n"), (85, 100))
        self.assertEqual(MODULE.cpu_used((80, 100), (170, 200)), 10.0)
        self.assertEqual(MODULE.meminfo(
            "MemTotal: 8000 kB\nMemAvailable: 6000 kB\n"
            "SwapTotal: 100 kB\nSwapFree: 90 kB\n"
        ), {"total_kib": 8000, "available_kib": 6000,
            "swap_used_kib": 10})

    def test_output_contract_is_content_free_and_idle_only(self):
        source = PATH.read_text()
        self.assertIn('rpc("Player.GetActivePlayers"', source)
        self.assertIn('rpc("GUI.GetProperties"', source)
        self.assertIn('{10000: "home", 13001: "aster-screensaver"}', source)
        self.assertIn('raise RuntimeError("idle-player-busy")', source)
        self.assertIn('raise RuntimeError("idle-player-started")', source)
        self.assertNotIn('"currentcontrol"', source)
        for forbidden in ("Player.GetItem", "title", "filename", "plot",
                          "VideoLibrary", "Player.Open", "Input."):
            self.assertNotIn(forbidden, source)

    def test_idle_window_classification_distinguishes_kodi_screensaver(self):
        self.assertEqual(MODULE.classify_window(10000), "home")
        self.assertEqual(MODULE.classify_window(13001), "aster-screensaver")
        self.assertEqual(MODULE.classify_window(10004), "other")

    def test_target_and_duration_fail_closed(self):
        with patch.object(MODULE.os, "uname") as uname:
            uname.return_value.nodename = "wrong-host"
            with self.assertRaisesRegex(RuntimeError, "idle-target"):
                MODULE.sample(2)
        with self.assertRaisesRegex(RuntimeError, "idle-duration"):
            MODULE.main(["--duration", "1"])


if __name__ == "__main__":
    unittest.main()
