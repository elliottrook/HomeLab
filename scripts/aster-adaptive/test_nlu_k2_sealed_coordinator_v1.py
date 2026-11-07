import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

import nlu_k2_sealed_coordinator_v1 as coordinator


def token(path, value):
    raw = (value + "\n").encode(); path.write_bytes(raw); os.chmod(path, 0o600)
    return hashlib.sha256(raw).hexdigest()


def session(relay_digest="a" * 64, upstream_digest="b" * 64):
    return {"schema": "aster-m3-k2-sealed-session.v1", "state": "ready",
            "workload_id": coordinator.WORKLOAD_ID,
            "booking_id": "aster-stream-a-m3-k2-sealed-20261107-1200-r1",
            "preregistration_sha256": coordinator.PREREGISTRATION_SHA256,
            "session_id": "k2-sealed-0123456789abcdef", "lease_id": "lease-7",
            "generation": 2, "start_epoch": 1000, "deadline_epoch": 2800,
            "request_count": 32, "retries": 0,
            "relay_nonce_sha256": relay_digest,
            "upstream_nonce_sha256": upstream_digest,
            "private_listener_port": 11436,
            "private_listener_scope": "aster-llama-k2-sealed-0123456789abcdef.scope",
            "production_masked": True, "operation_lock_held": True,
            "authority": "not-granted"}


class K2SealedCoordinatorTests(unittest.TestCase):
    def test_session_and_tokens_are_exact_and_distinct(self):
        value = session()
        self.assertEqual(value, coordinator.validate_session(value, now_epoch=1001))
        value["upstream_nonce_sha256"] = value["relay_nonce_sha256"]
        with self.assertRaises(coordinator.CoordinatorError):
            coordinator.validate_session(value, now_epoch=1001)

    def test_commands_pin_two_loopback_tunnels_and_no_secret(self):
        commands = coordinator.commands(
            "k2-sealed-0123456789abcdef", Path("/private/relay"),
            Path("/private/upstream"))
        self.assertIn("127.0.0.1:11439:192.168.70.12:11436",
                      commands["upstream_tunnel"])
        self.assertIn("127.0.0.1:11437:127.0.0.1:11438",
                      commands["reverse_tunnel"])
        encoded = repr(commands)
        self.assertNotIn("relay-secret", encoded)
        self.assertNotIn("upstream-secret", encoded)

    def test_token_custody_and_cleanup_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            digest = token(path, "r" * 32)
            self.assertEqual("r" * 32, coordinator._token(path, digest))
            os.chmod(path, 0o644)
            with self.assertRaises(coordinator.CoordinatorError):
                coordinator._token(path, digest)

    def test_rejects_stale_session_before_process_start(self):
        value = session()
        with self.assertRaises(coordinator.CoordinatorError):
            coordinator.validate_session(value, now_epoch=2800)


if __name__ == "__main__":
    unittest.main()
