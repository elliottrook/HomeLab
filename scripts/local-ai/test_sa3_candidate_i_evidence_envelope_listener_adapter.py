import unittest

import aster_llama_sa3_candidate_i_evidence_envelope_wrapper as wrapper
import sa3_candidate_i_evidence_envelope_listener_adapter as adapter


class CandidateIListenerAdapterTests(unittest.TestCase):
    def test_guest_failure_parser_uses_last_bounded_json_line(self):
        value = (b"proxmox transport note\n"
                 b'{"state":"no_go","code":"candidate-i result errors:count=2;classes=ValueError"}\n'
                 b"scope cleanup note\n")
        self.assertEqual("candidate-i result errors:count=2;classes=ValueError",
                         adapter.bounded_guest_failure(value))
        self.assertEqual("unclassified guest failure",
                         adapter.bounded_guest_failure(b"traceback only\n"))
        self.assertEqual("unclassified guest failure",
                         adapter.bounded_guest_failure(
                             ('{"code":"' + 'x' * 161 + '"}\n').encode()))

    def test_guest_failure_parser_checks_stdout_and_projects_no_content(self):
        self.assertEqual(
            "candidate-i result errors:count=1;classes=TimeoutError",
            adapter.bounded_guest_failure(
                b"transport only\n",
                b'prefix:{"code":"candidate-i result errors:count=1;classes=TimeoutError"}\n',
                1))
        self.assertEqual(
            "candidate-i guest traceback-class:KeyboardInterrupt",
            adapter.bounded_guest_failure(
                b'Traceback (most recent call last):\nKeyboardInterrupt: private\n',
                b"", 1))
        self.assertEqual(
            "candidate-i guest exit-status:137;stdout-bytes:0;stderr-bytes:0",
            adapter.bounded_guest_failure(b"", b"", 137))
        self.assertNotIn(
            "private", adapter.bounded_guest_failure(
                b"KeyError: private\n", b"", 1))

    def test_command_is_fixed_and_carries_no_arbitrary_command(self):
        command = adapter.listener_command(lease_id="lease-1", generation=2)
        self.assertEqual(("pct", "exec", "110", "--"), command[:4])
        self.assertEqual(("/usr/bin/python3", "-B"), command[4:6])
        self.assertIn("aster_llama_sa3_candidate_i_evidence_envelope_wrapper.py",
                      command[6])
        self.assertIn(adapter.WORKLOAD_ID, command)
        self.assertEqual("20", command[command.index("--requests") + 1])
        self.assertEqual("2700", command[command.index("--deadline") + 1])
        supplied = command[command.index("--scope-unit") + 1]
        self.assertEqual(wrapper._scope_unit("lease-1", 2), supplied)
        self.assertTrue(supplied.startswith("aster-llama-sa3-i-"))

    def test_invalid_lease_identity_fails_before_process(self):
        with self.assertRaises(adapter.AdapterError):
            adapter.listener_command(lease_id="bad lease", generation=1)

    def test_invalid_deadline_fails_before_process(self):
        with self.assertRaisesRegex(adapter.AdapterError, "deadline"):
            adapter.run(lease_id="lease-1", generation=1, deadline_epoch=5000,
                        heartbeat=lambda: None, clock=lambda: 0)


if __name__ == "__main__":
    unittest.main()

