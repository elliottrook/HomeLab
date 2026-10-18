import json
import unittest

from full_inference_lab_workload import (LAB_COMMAND, LAB_PROFILE, LabWorkloadError,
                                         lab_command, lab_is_absent, run_fixed_smoke,
                                         validate_receipt)


class FullInferenceLabWorkloadTests(unittest.TestCase):
    def receipt(self, **updates):
        value = {
            "schema": "aster-9b-direct-control-smoke.v1",
            "profile": LAB_PROFILE,
            "lease_id": "lease-1",
            "generation": 2,
            "port": 11436,
            "production_service": "masked-inactive",
            "credential_exported": False,
            "tool_mode": "disabled",
            "request_count": 3,
            "observation_ids": ["a", "b", "c"],
            "exit_status": 0,
        }
        value.update(updates)
        return value

    def test_fixed_command_is_distinct_from_production_service(self):
        self.assertIn("aster-llama-lab-smoke", " ".join(LAB_COMMAND))
        self.assertIn("11436", LAB_COMMAND)
        self.assertNotIn("aster-llama.service", LAB_COMMAND)

    def test_accepts_only_content_free_three_request_receipt(self):
        value = validate_receipt(self.receipt(), lease_id="lease-1", generation=2)
        self.assertEqual(value["request_count"], 3)

    def test_runner_never_returns_raw_answers(self):
        seen = []
        def runner(command, timeout):
            seen.append((tuple(command), timeout))
            return 0, json.dumps(self.receipt())
        value = run_fixed_smoke(runner, lease_id="lease-1", generation=2)
        self.assertNotIn("answer", value)
        self.assertEqual(seen, [(lab_command(lease_id="lease-1", generation=2), 300.0)])

    def test_rejects_production_or_credential_drift(self):
        for updates in ({"production_service": "active"}, {"credential_exported": True},
                        {"port": 11435}, {"request_count": 20}):
            with self.subTest(updates=updates):
                with self.assertRaises(LabWorkloadError):
                    validate_receipt(self.receipt(**updates), lease_id="lease-1", generation=2)

    def test_bounded_process_is_killed_on_deadline(self):
        class FakeProcess:
            pid = 123
            def __init__(self): self.returncode = None; self.killed = False
            def poll(self): return self.returncode
            def communicate(self): return "", ""
            def terminate(self): self.killed = True; self.returncode = 143
            def wait(self, timeout=None): self.returncode = 143
            def kill(self): self.killed = True; self.returncode = 137
        process = FakeProcess()
        from full_inference_lab_workload import run_fixed_smoke_bounded
        with self.assertRaises(LabWorkloadError):
            run_fixed_smoke_bounded(process_factory=lambda *a, **k: process,
                heartbeat=lambda: None, deadline=0, monotonic=lambda: 1,
                poll_seconds=0, lease_id="lease-1", generation=2)
        self.assertTrue(process.killed)

    def test_gpu_handle_probe_requires_explicit_no_handle_exit(self):
        calls = []
        def runner(command, timeout):
            calls.append(tuple(command))
            return ((1, "") if len(calls) in (1, 3, 4) else (0, ""))
        self.assertTrue(lab_is_absent(runner, lease_id="lease-1", generation=2))

    def test_gpu_handle_or_probe_error_blocks_absence(self):
        for result in ((0, "/proc/42/fd/7\\n"), (2, "")):
            with self.subTest(result=result):
                calls = []
                def runner(command, timeout):
                    calls.append(tuple(command))
                    return result if len(calls) == 4 else (1, "")
                self.assertFalse(lab_is_absent(runner, lease_id="lease-1", generation=2))


if __name__ == "__main__":
    unittest.main()
