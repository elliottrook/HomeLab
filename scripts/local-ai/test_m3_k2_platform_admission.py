import unittest

import aster_llama_m3_k2_development_wrapper as wrapper
import full_inference_lab_runtime as runtime
import m3_k2_development_listener_adapter as listener
import m3_k2_development_transaction as transaction
from test_m3_k2_development_transaction import valid_result


class K2PlatformAdmissionTests(unittest.TestCase):
    def test_runtime_parser_accepts_only_registered_profile(self):
        args = runtime._parser().parse_args((
            "--phase", "pilot", "--owner-id", "owner",
            "--workload-profile", transaction.WORKLOAD_ID,
        ))
        self.assertEqual(transaction.WORKLOAD_ID, args.workload_profile)

    def test_listener_command_is_fixed(self):
        command = listener.listener_command(lease_id="lease-1", generation=2)
        self.assertEqual("pct", command[0])
        self.assertIn(transaction.WORKLOAD_ID, command)
        self.assertIn("192", command)
        self.assertIn("45", command)
        self.assertIn("1800", command)
        self.assertTrue(listener.k2_scope_unit("lease-1", 2).endswith(".scope"))

    def test_guest_and_host_accept_same_bounded_result(self):
        value = valid_result(True)
        wrapper.validate_result(value)
        metadata = transaction.validate_result(value)
        self.assertTrue(metadata["development_gate_passed"])

    def test_guest_rejects_request_count_drift(self):
        value = valid_result(True)
        value["run"]["attempted"] = 191
        with self.assertRaises(wrapper.GuestError):
            wrapper.validate_result(value)


if __name__ == "__main__":
    unittest.main()
