import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate-aster-arr-report.py"
RECEIVER = ROOT / "scripts/receive-aster-arr-report.sh"


def receiver_validator(report: dict) -> subprocess.CompletedProcess[str]:
    script = RECEIVER.read_text(encoding="utf-8")
    validation = script.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "report.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-", str(path)],
            input=validation,
            capture_output=True,
            check=False,
            text=True,
        )


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


class ReceiverValidatorTests(unittest.TestCase):
    def report(self) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "schema_version": 1,
            "generated_at": now.isoformat(),
            "services": {
                "radarr": {
                    "status": "warning",
                    "coverage": ["health", "queue"],
                    "queue_pending": 1,
                    "queue_errors": 1,
                    "import_pending": None,
                    "import_errors": None,
                }
            },
            "repair_candidates": [],
        }

    def test_accepts_exact_fresh_report(self):
        completed = receiver_validator(self.report())
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_rejects_private_status_and_overlong_candidate(self):
        report = self.report()
        report["services"]["radarr"]["status"] = "private response detail"
        self.assertNotEqual(receiver_validator(report).returncode, 0)

        report = self.report()
        generated_at = datetime.fromisoformat(report["generated_at"])
        report["repair_candidates"] = [
            {
                "operation": "dismiss_stale_radarr_queue_record",
                "service": "radarr",
                "candidate_ref": "radarr-q-abcdefghijklmnop",
                "expires_at": (generated_at.replace(microsecond=0) + timedelta(minutes=6)).isoformat(),
            }
        ]
        self.assertNotEqual(receiver_validator(report).returncode, 0)


if __name__ == "__main__":
    unittest.main()
