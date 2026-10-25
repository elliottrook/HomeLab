import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from evaluation_lease_entrypoint import EntryPointError, main, validate_phase_intent


class EntryPointTests(unittest.TestCase):
    def test_default_entrypoint_is_inert_without_reading_intent(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main([
                "--phase", "acquire", "--state", "/absent/state",
                "--intent", "/absent/intent",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue()),
                         {"effects": "disabled", "state": "source-only"})

    def test_effectful_path_requires_strict_intent(self):
        with self.assertRaises(Exception):
            # The effect flag is deliberately not used here; this only proves
            # the strict loader rejects malformed input before any adapter call.
            from evaluation_lease_entrypoint import load_intent
            path = Path("/tmp/stream-a-invalid-intent.json")
            path.write_text("[]\n")
            try:
                load_intent(path)
            finally:
                path.unlink()

    def test_phase_schemas_reject_extra_keys_and_string_booleans(self):
        with self.assertRaises(EntryPointError):
            validate_phase_intent("heartbeat", {
                "lease_id": "x", "generation": 1, "now_epoch": 1, "extra": 1,
            })
        restore = {
            "lease_id": "x", "generation": 1,
            "restored_baseline": {"units": [], "timers": []},
            "backend_active": True, "endpoint_authenticated": True,
            "endpoint_idle": True, "gpu_holders": [], "recovery": "false",
        }
        with self.assertRaises(EntryPointError):
            validate_phase_intent("restore", restore)
        restore["recovery"] = False
        restore["unexpected"] = 1
        with self.assertRaises(EntryPointError):
            validate_phase_intent("restore", restore)

    def test_effectful_path_rejects_arbitrary_state_path_without_reading(self):
        output = io.StringIO()
        with patch("evaluation_lease_entrypoint.load_intent") as load_intent:
            with redirect_stdout(output):
                code = main([
                    "--phase", "heartbeat", "--state", "/tmp/arbitrary-state",
                    "--intent", "/absent/intent", "--effect-authorized",
                ])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["effects"], "failed-closed")
        load_intent.assert_not_called()


if __name__ == "__main__":
    unittest.main()
