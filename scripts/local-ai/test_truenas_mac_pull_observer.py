import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("truenas_mac_pull_observer", Path(__file__).parents[2] / "services/local-ai-lease/truenas_mac_pull_observer.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class MacPullObserverTests(unittest.TestCase):
    def test_summary_contains_only_aggregate_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "nested" / "private.txt").write_text("secret")
            task = [{"id": 2, "enabled": True, "job": {"state": "SUCCESS", "arguments": [2], "time_finished": {"$date": 1791972002000}}}]
            with patch.object(MODULE, "ROOT", root), patch.object(MODULE.subprocess, "check_output", return_value=json.dumps(task)), patch.object(MODULE.time, "time", return_value=1791972010):
                receipt = MODULE.build_receipt()
        self.assertEqual(receipt["path"], str(root) + "/")
        self.assertEqual(receipt["entry_count"], 1)
        self.assertEqual(receipt["claim"], "tree-present-only")
        self.assertNotIn("private.txt", json.dumps(receipt))
        self.assertNotIn("secret", json.dumps(receipt))

    def test_rejects_unsuccessful_or_wrong_task(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(MODULE, "ROOT", Path(directory)), patch.object(MODULE.subprocess, "check_output", return_value=json.dumps([{"id": 1}])):
                with self.assertRaisesRegex(RuntimeError, "task-2"):
                    MODULE.build_receipt()


if __name__ == "__main__":
    unittest.main()
