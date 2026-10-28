import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from produce_aster_agent_log_report import COMMAND, atomic_write, collect_report


NOW = datetime(2026, 10, 28, 23, 30, tzinfo=timezone.utc)
FIELDS = {
    "PRIORITY": "3", "_BOOT_ID": "a", "__CURSOR": "b",
    "__MONOTONIC_TIMESTAMP": "1", "__REALTIME_TIMESTAMP": "1793230200000000",
    "__SEQNUM": "2", "__SEQNUM_ID": "c",
}


class AsterAgentLogReportProducerTests(unittest.TestCase):
    def runner(self, stdout="", stderr="", returncode=0):
        def run(command, **kwargs):
            self.assertEqual(list(COMMAND), command)
            self.assertNotIn("MESSAGE", " ".join(command))
            self.assertEqual({"LC_ALL": "C"}, kwargs["env"])
            return subprocess.CompletedProcess(command, returncode, stdout, stderr)
        return run

    def test_collects_count_without_messages(self):
        report = collect_report(
            now=NOW, runner=self.runner(json.dumps(FIELDS) + "\n")
        )
        self.assertEqual(1, report["high_priority_event_count"])
        self.assertEqual("aster-agent-journal", report["source"])
        self.assertEqual(900, report["window_seconds"])
        self.assertNotIn("private", json.dumps(report))

    def test_rejects_extra_fields_bad_priority_and_failure(self):
        for runner in (
            self.runner(json.dumps({**FIELDS, "MESSAGE": "private"}) + "\n"),
            self.runner(json.dumps({**FIELDS, "PRIORITY": "6"}) + "\n"),
            self.runner(stderr="failure"), self.runner(returncode=1),
        ):
            with self.subTest(runner=runner), self.assertRaises(ValueError):
                collect_report(now=NOW, runner=runner)

    def test_atomic_write_has_bounded_custody(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            value = collect_report(now=NOW, runner=self.runner())
            atomic_write(path, value, uid=os.getuid(), gid=os.getgid())
            self.assertEqual(value, json.loads(path.read_text()))
            self.assertEqual(0o640, path.stat().st_mode & 0o777)


if __name__ == "__main__":
    unittest.main()
