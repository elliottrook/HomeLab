import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate-aster-arr-report.py"


class ValidatorCommandTests(unittest.TestCase):
    def test_validates_fresh_report_without_network_access(self):
        report = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "services": {
                "radarr": {
                    "status": "healthy",
                    "coverage": ["health", "queue", "import"],
                    "queue_pending": 0,
                    "queue_errors": 0,
                    "import_pending": 0,
                    "import_errors": 0,
                }
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True,
                check=False,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("operator-produced sanitized ARR report", completed.stdout)


if __name__ == "__main__":
    unittest.main()
