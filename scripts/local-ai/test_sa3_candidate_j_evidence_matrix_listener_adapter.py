import unittest

import sa3_candidate_j_evidence_matrix_listener_adapter as adapter


class CandidateJListenerAdapterTests(unittest.TestCase):
    def test_guest_failure_parser_projects_no_content(self):
        self.assertEqual(
            "candidate-j result errors:count=1;classes=TimeoutError",
            adapter.bounded_guest_failure(
                b"transport only\n",
                b'prefix:{"code":"candidate-j result errors:count=1;classes=TimeoutError"}\n',
                1))
        self.assertEqual(
            "candidate-j guest traceback-class:KeyboardInterrupt",
            adapter.bounded_guest_failure(
                b"Traceback (most recent call last):\nKeyboardInterrupt: private\n",
                b"", 1))
        self.assertEqual(
            "candidate-j guest exit-status:137;stdout-bytes:0;stderr-bytes:0",
            adapter.bounded_guest_failure(b"", b"", 137))
        self.assertNotIn(
            "private", adapter.bounded_guest_failure(
                b"KeyError: private\n", b"", 1))

    def test_command_is_fixed_and_carries_no_arbitrary_command(self):
        command = adapter.listener_command(lease_id="lease-1", generation=2)
        self.assertEqual(("pct", "exec", "110", "--"), command[:4])
        self.assertEqual(("/usr/bin/python3", "-B"), command[4:6])
        self.assertIn("aster_llama_sa3_candidate_j_evidence_matrix_wrapper.py",
                      command[6])
        self.assertIn(adapter.WORKLOAD_ID, command)
        self.assertEqual("6", command[command.index("--requests") + 1])
        self.assertEqual("1800", command[command.index("--deadline") + 1])
        supplied = command[command.index("--scope-unit") + 1]
        self.assertEqual(adapter.candidate_j_scope_unit("lease-1", 2), supplied)
        self.assertTrue(supplied.startswith("aster-llama-sa3-j-"))

    def test_invalid_lease_or_deadline_fails_before_process(self):
        with self.assertRaises(adapter.AdapterError):
            adapter.listener_command(lease_id="bad lease", generation=1)
        with self.assertRaisesRegex(adapter.AdapterError, "deadline"):
            adapter.run(lease_id="lease-1", generation=1,
                        deadline_epoch=5000, heartbeat=lambda: None,
                        clock=lambda: 0)


if __name__ == "__main__":
    unittest.main()
