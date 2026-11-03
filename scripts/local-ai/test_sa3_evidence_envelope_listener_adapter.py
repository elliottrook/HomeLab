import unittest

import sa3_evidence_envelope_listener_adapter as adapter


class CandidateGListenerAdapterTests(unittest.TestCase):
    def test_command_is_fixed_and_carries_no_arbitrary_command(self):
        command = adapter.listener_command(lease_id="lease-1", generation=2)
        self.assertEqual(("pct", "exec", "110", "--"), command[:4])
        self.assertIn("aster_llama_sa3_evidence_envelope_wrapper.py", command[4])
        self.assertIn(adapter.WORKLOAD_ID, command)
        self.assertEqual("20", command[command.index("--requests") + 1])
        self.assertEqual("2700", command[command.index("--deadline") + 1])

    def test_invalid_lease_identity_fails_before_process(self):
        with self.assertRaises(adapter.AdapterError):
            adapter.listener_command(lease_id="bad lease", generation=1)

    def test_invalid_deadline_fails_before_process(self):
        with self.assertRaisesRegex(adapter.AdapterError, "deadline"):
            adapter.run(lease_id="lease-1", generation=1, deadline_epoch=5000,
                        heartbeat=lambda: None, clock=lambda: 0)


if __name__ == "__main__":
    unittest.main()
