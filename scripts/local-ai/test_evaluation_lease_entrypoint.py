import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from evaluation_lease_entrypoint import EntryPointError, main, validate_phase_intent


class EntryPointTests(unittest.TestCase):
    def exercise_intent(self):
        return {
            "lease_id": "exercise-20261025-1", "generation": 1,
            "exercise_marker": "PRE-EFFECT-EXERCISE-NOT-PRODUCTION-EVIDENCE",
            "model": "Qwen3.5 9B Q4_K_M",
            "backend": "llama.cpp b11429 SYCL/Level Zero",
            "endpoint": "http://192.168.70.12:11435/v1/chat/completions",
            "backend_active": True, "endpoint_authenticated": True,
            "endpoint_idle": True, "gpu_holders": ["lxc110:aster-llama.service"],
            "registered_targets": [
                "lxc104:aster-agent.service", "lxc116:aster-speech.service",
                "lxc114:news-aggregator-ingest.timer",
                "lxc114:news-aggregator-digest.timer",
            ], "quiesced_targets": [],
            "baseline": {
                "units": [["lxc104:aster-agent.service", "enabled+active"],
                          ["lxc116:aster-speech.service", "enabled+active"]],
                "timers": [["lxc114:news-aggregator-ingest.timer", "enabled+active"],
                           ["lxc114:news-aggregator-digest.timer", "enabled+active"]],
            }, "watchdog_independent": True, "hard_deadline_epoch": 1120,
            "restore_deadline_epoch": 1300, "now_epoch": 1000,
        }

    def test_exercise_schema_has_no_receipts_and_is_exact(self):
        value = self.exercise_intent()
        validate_phase_intent("exercise-prepare", value)
        self.assertFalse(any("receipt" in key for key in value))
        with self.assertRaises(EntryPointError):
            validate_phase_intent("exercise-prepare", {**value, "f2_receipt": "fake"})
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

        with self.assertRaises(EntryPointError):
            validate_phase_intent("quiesce", {
                "lease_id": "x", "generation": 1, "now_epoch": 1,
                "heartbeat_timeout": 30, "unexpected": False,
            })
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

    def test_wrapper_disabled_invocation_leaves_no_bytecode(self):
        source_root = Path(__file__).resolve().parent
        wrapper_source = source_root.parent.parent / "services/local-ai-lease/stream-a-evaluation-lease"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "stream-a-evaluation"
            root.mkdir()
            for name in ("evaluation_lease.py", "evaluation_lease_adapter.py",
                         "evaluation_lease_watchdog.py", "host_exclusion.py",
                         "evaluation_lease_entrypoint.py"):
                shutil.copy2(source_root / name, root / name)
            wrapper = Path(temp_dir) / "wrapper"
            wrapper.write_text(wrapper_source.read_text().replace(
                "/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py",
                str(root / "evaluation_lease_entrypoint.py")))
            wrapper.chmod(0o755)
            result = subprocess.run(
                ["/bin/sh", str(wrapper), "--phase", "acquire",
                 "--state", "/absent/state", "--intent", "/absent/intent"],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(json.loads(result.stdout),
                             {"effects": "disabled", "state": "source-only"})
            self.assertEqual(
                sorted(path.relative_to(root).as_posix() for path in root.rglob("*")),
                sorted(name for name in ("evaluation_lease.py", "evaluation_lease_adapter.py",
                                         "evaluation_lease_watchdog.py", "host_exclusion.py",
                                         "evaluation_lease_entrypoint.py")),
            )


if __name__ == "__main__":
    unittest.main()
