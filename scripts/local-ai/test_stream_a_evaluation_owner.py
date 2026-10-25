import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stream_a_evaluation_owner import EXERCISE_OWNER_UNIT, build_identity, main


class OwnerProcessTests(unittest.TestCase):
    def identity(self):
        return {
            "lease_id": "exercise-1", "generation": 1, "heartbeat_timeout": 5,
            "owner_id": "exercise-owner", "pid": 42, "boot_id": "boot-1",
            "starttime_ticks": 99, "cmdline": "/owner --exercise-transient",
            "unit": EXERCISE_OWNER_UNIT,
        }

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

    def test_exercise_identity_uses_only_the_fixed_transient_unit(self):
        with tempfile.TemporaryDirectory() as root:
            intent = Path(root) / "owner-intent.json"
            intent.write_text(json.dumps({"lease_id": "exercise-1", "generation": 1,
                                          "heartbeat_timeout": 5,
                                          "owner_id": "exercise-owner"}) + "\n")
            intent.chmod(0o600)
            with patch("stream_a_evaluation_owner._starttime_ticks", return_value=99), \
                 patch("stream_a_evaluation_owner.Path.read_text", return_value="boot-1\n"), \
                 patch("stream_a_evaluation_owner.Path.read_bytes", return_value=b"/owner\0"):
                value = build_identity(intent, pid=42, required_uid=os.geteuid(),
                                       unit=EXERCISE_OWNER_UNIT)
            self.assertEqual(value["unit"], EXERCISE_OWNER_UNIT)
            with self.assertRaisesRegex(ValueError, "not an allowed fixed identity"):
                build_identity(intent, pid=42, required_uid=os.geteuid(),
                               unit="attacker-selected.service")

    def test_exercise_main_refuses_wrong_cgroup_before_writing_identity(self):
        with patch("stream_a_evaluation_owner.os.geteuid", return_value=0), \
             patch("stream_a_evaluation_owner.build_identity", return_value=self.identity()), \
             patch("stream_a_evaluation_owner.owner_process_matches", return_value=False), \
             patch("stream_a_evaluation_owner._write_identity") as write:
            self.assertEqual(main(["--run", "--effect-authorized",
                                   "--exercise-transient"]), 1)
        write.assert_not_called()

    def test_exercise_main_writes_only_after_exact_cgroup_match(self):
        with patch("stream_a_evaluation_owner.os.geteuid", return_value=0), \
             patch("stream_a_evaluation_owner.build_identity", return_value=self.identity()), \
             patch("stream_a_evaluation_owner.owner_process_matches", return_value=True), \
             patch("stream_a_evaluation_owner._write_identity") as write, \
             patch("stream_a_evaluation_owner.signal.signal"), \
             patch("stream_a_evaluation_owner._running", False):
            self.assertEqual(main(["--run", "--effect-authorized",
                                   "--exercise-transient"]), 0)
        write.assert_called_once_with(self.identity())


if __name__ == "__main__":
    unittest.main()
