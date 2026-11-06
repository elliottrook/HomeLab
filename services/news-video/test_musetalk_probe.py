import json
from pathlib import Path
import tempfile
import unittest

import musetalk_probe


LIGHTROOM_HELPER = (
    "/Applications/Adobe Lightroom Classic/Adobe Lightroom Classic.app/Contents/"
    "Frameworks/AdobeCrashReporter.framework/Versions/A/Adobe Crash Processor.app/"
    "Contents/MacOS/Adobe Crash Processor"
)


class MuseTalkProbeTests(unittest.TestCase):
    def test_mac_attended_contract_keeps_the_first_step_tiny(self):
        manifest = json.loads(musetalk_probe.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            loaded = musetalk_probe.load_manifest(path)
        self.assertEqual(loaded["probe"]["frames"], 1)
        self.assertEqual(loaded["probe"]["batch_size"], 1)
        self.assertEqual(loaded["safety"]["minimum_free_percent_at_start"], 40)
        self.assertEqual(loaded["safety"]["minimum_free_percent_while_running"], 20)

    def test_forbidden_processes_are_narrow(self):
        rows = [
            (1, 0, 100, "/Applications/ChatGPT.app/Contents/MacOS/ChatGPT"),
            (2, 0, 100, "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        ]
        matches = musetalk_probe.forbidden_processes(rows)
        self.assertEqual(len(matches), 1)
        self.assertIn("Brave Browser", matches[0])

    def test_lightroom_crash_helper_is_not_the_editor(self):
        rows = [(2, 0, 100, LIGHTROOM_HELPER)]
        self.assertEqual(musetalk_probe.forbidden_processes(rows), [])

    def test_process_tree_rss_excludes_unrelated_processes(self):
        rows = [
            (10, 1, 1000, "worker"),
            (11, 10, 2000, "child"),
            (12, 11, 3000, "grandchild"),
            (20, 1, 9000, "unrelated"),
        ]
        self.assertEqual(musetalk_probe.process_tree_rss_bytes(10, rows), 6000 * 1024)

    def test_exclusion_lock_rejects_a_second_holder(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exclusive.lock"
            with musetalk_probe.acquire_exclusion_lock(path):
                with self.assertRaises(musetalk_probe.ProbeError):
                    musetalk_probe.acquire_exclusion_lock(path)


if __name__ == "__main__":
    unittest.main()
