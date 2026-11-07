import copy
import unittest

import m3_k2_sealed_session_contract as contract


def ready():
    return {"schema": "aster-m3-k2-sealed-session.v1", "state": "ready",
            "workload_id": contract.WORKLOAD_ID,
            "booking_id": "aster-stream-a-m3-k2-sealed-20261107-1200-r1",
            "preregistration_sha256": contract.PREREGISTRATION_SHA256,
            "session_id": "k2-sealed-0123456789abcdef", "lease_id": "lease-7",
            "generation": 2, "start_epoch": 1000, "deadline_epoch": 2800,
            "request_count": 32, "retries": 0,
            "relay_nonce_sha256": "a" * 64,
            "upstream_nonce_sha256": "b" * 64,
            "private_listener_port": 11436,
            "private_listener_scope": "aster-llama-k2-sealed-0123456789abcdef.scope",
            "production_masked": True, "operation_lock_held": True,
            "authority": "not-granted"}


def terminal(state="complete"):
    return {"schema": "aster-m3-k2-sealed-terminal.v1", "state": state,
            "workload_id": contract.WORKLOAD_ID,
            "booking_id": "aster-stream-a-m3-k2-sealed-20261107-1200-r1",
            "session_id": "k2-sealed-0123456789abcdef",
            "model_requests": 32 if state == "complete" else 7,
            "retries": 0, "response_errors": 0 if state == "complete" else 1,
            "records_sha256": "c" * 64 if state == "complete" else None,
            "metrics_sha256": "d" * 64 if state == "complete" else None,
            "production_restored": True, "lease_ready": True,
            "locks_absent": True, "private_listener_absent": True,
            "relay_absent": True, "runner_absent": True, "tunnels_absent": True,
            "failure_code": None if state == "complete" else "RELAY_UNAVAILABLE",
            "authority": "not-granted"}


class K2SealedSessionContractTests(unittest.TestCase):
    def test_ready_session_binds_booking_lease_nonces_and_deadline(self):
        result = contract.validate_ready(ready(), now_epoch=1001)
        self.assertEqual(32, result["request_count"])
        self.assertEqual(2, result["generation"])

    def test_ready_rejects_stale_or_same_nonce(self):
        with self.assertRaises(contract.ContractError):
            contract.validate_ready(ready(), now_epoch=2800)
        value = ready(); value["upstream_nonce_sha256"] = "a" * 64
        with self.assertRaises(contract.ContractError):
            contract.validate_ready(value, now_epoch=1001)

    def test_complete_terminal_requires_full_restoration(self):
        result = contract.validate_terminal(terminal())
        self.assertEqual("complete", result["state"])
        for field in ("production_restored", "lease_ready", "locks_absent",
                      "private_listener_absent", "relay_absent",
                      "runner_absent", "tunnels_absent"):
            value = terminal(); value[field] = False
            with self.assertRaises(contract.ContractError):
                contract.validate_terminal(value)

    def test_no_go_retains_bounded_first_failure(self):
        result = contract.validate_terminal(terminal("no_go"))
        self.assertEqual("RELAY_UNAVAILABLE", result["failure_code"])
        value = terminal("no_go"); value["failure_code"] = "private text"
        with self.assertRaises(contract.ContractError):
            contract.validate_terminal(value)

    def test_complete_is_exactly_32_zero_error_requests(self):
        for field, changed in (("model_requests", 31),
                               ("response_errors", 1),
                               ("failure_code", "UNEXPECTED")):
            value = terminal(); value[field] = changed
            with self.assertRaises(contract.ContractError):
                contract.validate_terminal(value)


if __name__ == "__main__":
    unittest.main()
