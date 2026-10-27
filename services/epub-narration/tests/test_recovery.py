from pathlib import Path
import json
import subprocess
import sys
import unittest


class RecoveryTests(unittest.TestCase):
    def test_isolated_regeneration(self):
        tool = Path(__file__).parents[1] / "tools" / "verify_recovery.py"
        result = subprocess.run([sys.executable, str(tool)], check=True, capture_output=True, text=True)
        self.assertEqual({"chapters": 1, "isolated": True, "ready": 1,
                          "state": "passed", "synthetic": True}, json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
