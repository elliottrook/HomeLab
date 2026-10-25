import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stream_a_evaluation_owner import build_identity


class OwnerProcessTests(unittest.TestCase):
    def test_owner_identity_is_persistent_process_bound_and_does_not_acquire(self):
        with tempfile.TemporaryDirectory() as root:
            intent = Path(root) / "owner-intent.json"
            intent.write_text(json.dumps({"lease_id": "eval-1", "generation": 1,
                                          "heartbeat_timeout": 30, "owner_id": "owner-1"}) + "\n")
            intent.chmod(0o600)
            with patch("stream_a_evaluation_owner._starttime_ticks", return_value=99), \
                 patch("stream_a_evaluation_owner.Path.read_text", return_value="boot-1\n"), \
                 patch("stream_a_evaluation_owner.Path.read_bytes", return_value=b"/owner\0"):
                value = build_identity(intent, pid=42, required_uid=os.geteuid())
            self.assertEqual(value["pid"], 42)
            self.assertEqual(value["starttime_ticks"], 99)
            self.assertEqual(value["unit"], "stream-a-evaluation-owner.service")
            self.assertNotIn("acquire", value)


if __name__ == "__main__":
    unittest.main()
