import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


PATH = Path(__file__).with_name("measure_page_latency.py")
SPEC = importlib.util.spec_from_file_location("measure_page_latency", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PageLatencyTests(unittest.TestCase):
    def test_routes_are_named_and_content_free(self):
        self.assertEqual(
            [(row[0], row[1]) for row in MODULE.ROUTES],
            [("books", 11110), ("news", 11111), ("home", 11112),
             ("music", 11113), ("cameras", 11134)],
        )
        source = PATH.read_text()
        for forbidden in ("Player.Open", "Player.GoTo", "Player.Seek",
                          "Files.GetDirectory", "VideoLibrary", "AudioLibrary",
                          "currentcontrol", "ListItem", "thumbnail", "plot"):
            self.assertNotIn(forbidden, source)
        self.assertIn('raise RuntimeError("page-player-busy")', source)
        self.assertIn('raise RuntimeError("page-player-started")', source)
        self.assertIn('action("ActivateWindow(Home)")', source)
        self.assertIn('raise RuntimeError("page-home-restore")', source)

    def test_result_contains_metrics_not_labels(self):
        with patch.object(MODULE, "active_players", return_value=[]), \
                patch.object(MODULE, "action"), \
                patch.object(MODULE, "counter", side_effect=[100, 200, 160, 230]), \
                patch.object(MODULE, "window_id", return_value=11134):
            row = MODULE.measure_route("cameras", 11134, None, None)
        self.assertEqual(row["page"], "cameras")
        self.assertEqual(row["network_rx_bytes"], 60)
        self.assertEqual(row["network_tx_bytes"], 30)
        self.assertIsNone(row["data_ready_ms"])
        self.assertTrue(row["within_budget"])
        self.assertEqual(set(row), {"page", "window_id", "activation_ms",
                                    "data_ready_ms", "network_rx_bytes",
                                    "network_tx_bytes", "within_budget"})

    def test_budgets_are_low_spec_bounded(self):
        self.assertEqual(MODULE.ACTIVATION_BUDGET_MS, 250.0)
        self.assertEqual(MODULE.DATA_READY_BUDGET_MS, 2000.0)
        self.assertEqual(MODULE.NETWORK_RX_BUDGET_BYTES, 262144)
        self.assertEqual(MODULE.NETWORK_TX_BUDGET_BYTES, 65536)

    def test_target_and_passes_fail_closed(self):
        with patch.object(MODULE.os, "uname") as uname:
            uname.return_value.nodename = "wrong-host"
            with self.assertRaisesRegex(RuntimeError, "page-target"):
                MODULE.run(1)
        with self.assertRaisesRegex(RuntimeError, "page-passes"):
            MODULE.main(["--passes", "0"])


if __name__ == "__main__":
    unittest.main()
