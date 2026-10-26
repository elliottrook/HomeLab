import io
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from evaluation_lease_entrypoint import EntryPointError, _main_effectful, main, validate_phase_intent
from stream_a_evaluation_admission import (
    ADMISSION_PREFIX, ADMISSION_SCHEMA, EXPECTED_BACKEND, EXPECTED_D4_DIGEST,
    EXPECTED_M3_DIGEST, EXPECTED_MODEL, F5_SCHEMA, canonical_bytes,
    load_bound_admission as real_load_bound_admission,
)


class EntryPointTests(unittest.TestCase):
    def acquire_intent(self, admission_receipt):
        return {
            "lease_id": "eval-1", "generation": 1,
            "backup_receipt": "retained-archive-integrity-sha256:" + "a" * 64,
            "f2_receipt": "f2-result-sha256:" + "b" * 64,
            "f3_receipt": "f3-receipt-sha256:" + "c" * 64,
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
            }, "watchdog_independent": True, "hard_deadline_epoch": 5500,
            "restore_deadline_epoch": 6400, "now_epoch": 1000,
            "admission_receipt": admission_receipt,
        }

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

    def test_acquire_binds_fixed_f5_admission_into_durable_state(self):
        import argparse
        with tempfile.TemporaryDirectory() as root:
            parent = Path(root) / "stream-a-evaluation"
            parent.mkdir(mode=0o700); parent.chmod(0o700)
            f5 = {
                "schema": F5_SCHEMA, "cycle_date": "2026-10-26",
                "observed_epoch": 999, "expires_epoch": 1800,
                "f2_result_sha256": "b" * 64, "f3_receipt_sha256": "c" * 64,
                "f4_receipt_sha256": "d" * 64,
                "lxc110_mirror_identity": "task2:success",
                "schedule_set_sha256": "e" * 64, "model": EXPECTED_MODEL,
                "binary_sha256": "f" * 64, "unit_sha256": "1" * 64,
                "auth_identity": "aster-llama-key-file-v1",
                "consumer_baseline_sha256": "2" * 64,
                "conflicting_lease": False, "conflicting_job": False,
            }
            f5_path = parent / "f5-observation.json"
            f5_raw = canonical_bytes(f5); f5_path.write_bytes(f5_raw); f5_path.chmod(0o600)
            admission = {
                "schema": ADMISSION_SCHEMA, "cycle_date": "2026-10-26",
                "lease_id": "eval-1", "generation": 1,
                "created_epoch": 999, "expires_epoch": 1800,
                "backup_receipt": "retained-archive-integrity-sha256:" + "a" * 64,
                "f2_result_sha256": "b" * 64, "f3_receipt_sha256": "c" * 64,
                "f4_receipt_sha256": "d" * 64,
                "f5_observation_sha256": hashlib.sha256(f5_raw).hexdigest(),
                "d4_run_digest": EXPECTED_D4_DIGEST,
                "m3_manifest_sha256": EXPECTED_M3_DIGEST,
                "model": EXPECTED_MODEL, "backend": EXPECTED_BACKEND,
            }
            admission_path = parent / "admission.json"
            admission_raw = canonical_bytes(admission)
            admission_path.write_bytes(admission_raw); admission_path.chmod(0o600)
            receipt = ADMISSION_PREFIX + hashlib.sha256(admission_raw).hexdigest()
            state = parent / "lease.json"
            args = argparse.Namespace(state=state, phase="acquire")
            test_uid = os.geteuid()
            with patch("evaluation_lease_entrypoint.DEFAULT_STATE_PATH", state), \
                    patch("evaluation_lease_entrypoint.ADMISSION_PATH", admission_path), \
                    patch("evaluation_lease_entrypoint.F5_OBSERVATION_PATH", f5_path), \
                    patch("evaluation_lease_entrypoint.load_bound_admission",
                          side_effect=lambda *a, **k: real_load_bound_admission(
                              *a, **k, required_uid=test_uid)), \
                    patch("evaluation_lease_entrypoint._is_root", return_value=True):
                result = _main_effectful(args, self.acquire_intent(receipt))
            self.assertEqual(result["effects"], "prepared")
            self.assertEqual(json.loads(state.read_text())["admission_receipt"], receipt)

    def test_wrapper_disabled_invocation_leaves_no_bytecode(self):
        source_root = Path(__file__).resolve().parent
        wrapper_source = source_root.parent.parent / "services/local-ai-lease/stream-a-evaluation-lease"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "stream-a-evaluation"
            root.mkdir()
            for name in ("evaluation_lease.py", "evaluation_lease_adapter.py",
                         "evaluation_lease_watchdog.py", "host_exclusion.py",
                         "evaluation_lease_entrypoint.py",
                         "stream_a_evaluation_admission.py"):
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
                                         "evaluation_lease_entrypoint.py",
                                         "stream_a_evaluation_admission.py")),
            )


if __name__ == "__main__":
    unittest.main()
