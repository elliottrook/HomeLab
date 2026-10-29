import json
import os
import unittest

import sa3_listener_adapter as adapter
from sa3_expanded_quality_transaction import PACKET_CASE_IDS, PACKET_SHA256, MODEL_ID


def result():
    return {"schema_version": 1, "packet_id": "sa3-expanded-source-quality-v1",
            "packet_sha256": PACKET_SHA256, "model": MODEL_ID,
            "request_count": 20, "retry_count": 0,
            "predictions": [{"id": ident, "outcome": "clarify", "checks": [],
                             "summary": "bounded", "effects": [],
                             "finish_reason": "stop", "latency_seconds": 0.1}
                            for ident in PACKET_CASE_IDS],
            "errors": []}


class Process:
    def __init__(self, output=None, status=0):
        self.pid = 1234; self.output = output; self.status = status; self.stopped = False
    def poll(self): return self.status
    def communicate(self, timeout=None): return self.output or "", ""
    def terminate(self): self.stopped = True
    def kill(self): self.stopped = True
    def wait(self, timeout=None): self.stopped = True


class AdapterTests(unittest.TestCase):
    def test_command_is_fixed_and_profile_bound(self):
        command = adapter.listener_command(lease_id="lease-1", generation=2)
        self.assertEqual(command[:5], ("pct", "exec", "110", "--", adapter.LISTENER))
        self.assertIn(("--profile", adapter.WORKLOAD_ID),
                      tuple(zip(command[5::2], command[6::2])))
        self.assertIn("120", command)
        self.assertIn("2700", command)

    def test_success_heartbeats_and_cleans_exact_process(self):
        process = Process(json.dumps(result()))
        calls = []; sleeps = []
        value = adapter.run(lease_id="lease-1", generation=2, deadline_epoch=100,
                            heartbeat=lambda: calls.append("heartbeat"),
                            process_factory=lambda *args, **kwargs: process,
                            clock=lambda: 1, sleep=lambda seconds: sleeps.append(seconds),
                            killpg=lambda pid, sig: calls.append((pid, sig)))
        self.assertEqual(value["request_count"], 20)
        self.assertEqual(calls, ["heartbeat"])
        self.assertFalse(process.stopped)

    def test_timeout_terminates_process_and_heartbeats(self):
        process = Process(None, status=None); calls = []
        now = iter((1, 101))
        with self.assertRaisesRegex(adapter.AdapterError, "deadline"):
            adapter.run(lease_id="lease-1", generation=2, deadline_epoch=100,
                        heartbeat=lambda: calls.append("heartbeat"),
                        process_factory=lambda *args, **kwargs: process,
                        clock=lambda: next(now), sleep=lambda seconds: None,
                        killpg=lambda pid, sig: calls.append((pid, sig)))
        self.assertIn("heartbeat", calls)
        self.assertTrue(process.stopped)

    def test_nonzero_malformed_and_oversized_output_fail_closed(self):
        for process, message in ((Process("{}", status=1), "nonzero"),
                                  (Process("not-json"), "not JSON"),
                                  (Process("x" * (adapter.RESULT_MAX_BYTES + 1)), "exceeded")):
            with self.subTest(message=message):
                with self.assertRaisesRegex(adapter.AdapterError, message):
                    adapter.run(lease_id="lease-1", generation=2, deadline_epoch=100,
                                heartbeat=lambda: None,
                                process_factory=lambda *args, p=process, **kwargs: p,
                                clock=lambda: 1, killpg=lambda *_: None)

    def test_no_arbitrary_command_or_invalid_identity(self):
        with self.assertRaisesRegex(adapter.AdapterError, "identity"):
            adapter.listener_command(lease_id="; reboot", generation=1)
        with self.assertRaises(TypeError):
            adapter.run(lease_id="lease-1", generation=1, deadline_epoch=100,
                        heartbeat=lambda: None, command=("sh", "-c", "false"))


if __name__ == "__main__": unittest.main()
