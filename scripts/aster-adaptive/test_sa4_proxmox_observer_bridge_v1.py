import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import sa4_observer_signer_v1 as observer
import sa4_proxmox_observer_bridge_v1 as bridge


STATEMENT = observer.canonical({
    "schema": "aster-sa4-independent-receipt-proof.v1",
    "receipt_sha256": "1" * 64,
    "observer_id": observer.OBSERVER_ID,
    "observer_key_sha256": observer.KEY_SHA256,
    "signature_algorithm": "rsa-pkcs1v1_5-sha256",
    "authority": "observer-proof-only-no-effect",
})


class SA4ProxmoxObserverBridgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "bridge"
        self.directory.mkdir(mode=0o700)
        self.patchers = (
            patch.object(bridge, "BRIDGE_DIRECTORY", self.directory),
            patch.object(bridge, "EXPECTED_UID", os.geteuid()),
        )
        for item in self.patchers: item.start(); self.addCleanup(item.stop)
        self.calls = []

    def runner(self, arguments, **kwargs):
        self.calls.append(arguments)
        if arguments[1] == "pull":
            destination = Path(arguments[4]); destination.write_bytes(STATEMENT)
            destination.chmod(0o600)
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    def test_exact_pull_sign_push_sequence(self):
        result = bridge.bridge(1, runner=self.runner,
                               signer=lambda raw: "a" * 512)
        self.assertEqual(["pull", "push"], [row[1] for row in self.calls])
        self.assertEqual("104", self.calls[0][2])
        self.assertEqual("104", self.calls[1][2])
        self.assertTrue(result["signature_written"])
        self.assertFalse(result["arbitrary_command"])

    def test_duplicate_and_bad_directory_fail_before_runner(self):
        bridge.bridge(1, runner=self.runner, signer=lambda raw: "a" * 512)
        with self.assertRaises(FileExistsError):
            bridge.bridge(1, runner=self.runner, signer=lambda raw: "a" * 512)
        self.directory.chmod(0o755)
        with self.assertRaises(ValueError):
            bridge.bridge(2, runner=self.runner, signer=lambda raw: "a" * 512)

    def test_pull_failure_does_not_sign_or_push(self):
        signed = []
        def failed(arguments, **kwargs):
            self.calls.append(arguments)
            return subprocess.CompletedProcess(arguments, 1, b"", b"failed")
        with self.assertRaises(RuntimeError):
            bridge.bridge(1, runner=failed,
                          signer=lambda raw: signed.append(raw) or "a" * 512)
        self.assertEqual([], signed)
        self.assertEqual(1, len(self.calls))

    def test_push_failure_retains_local_evidence(self):
        def fail_push(arguments, **kwargs):
            result = self.runner(arguments, **kwargs)
            if arguments[1] == "push": result.returncode = 1
            return result
        with self.assertRaises(RuntimeError):
            bridge.bridge(1, runner=fail_push, signer=lambda raw: "a" * 512)
        self.assertTrue((self.directory / "request-1.json").exists())
        self.assertTrue((self.directory / "response-1.signature").exists())


if __name__ == "__main__":
    unittest.main()
