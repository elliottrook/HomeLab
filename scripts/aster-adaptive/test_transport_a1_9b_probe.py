import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import transport_a1_9b_probe


class ProbeTransportTests(unittest.TestCase):
    def test_raw_synthetic_output_is_private_and_not_printed(self):
        packet = {"schema_version": "aster-answer-capture.v0", "tool_mode": "disabled",
                  "attempts": [{"case_id": "source-fact-01", "status": "completed",
                                "answer": "fictional private-to-review response"}]}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            printed = io.StringIO()
            with (patch.object(sys, "argv", ["transport", str(output)]),
                  patch.object(transport_a1_9b_probe.subprocess, "run",
                               return_value=SimpleNamespace(returncode=0,
                                                            stdout=json.dumps(packet))),
                  contextlib.redirect_stdout(printed)):
                transport_a1_9b_probe.main()
            self.assertEqual(json.loads(output.read_text())["attempts"][0]["answer"],
                             "fictional private-to-review response")
            self.assertEqual(os.stat(output).st_mode & 0o777, 0o600)
            self.assertNotIn("fictional private-to-review", printed.getvalue())

    def test_existing_output_refuses_uncertain_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            output.write_text("existing")
            with (patch.object(sys, "argv", ["transport", str(output)]),
                  patch.object(transport_a1_9b_probe.subprocess, "run") as remote):
                with self.assertRaises(SystemExit):
                    transport_a1_9b_probe.main()
                remote.assert_not_called()


if __name__ == "__main__":
    unittest.main()
