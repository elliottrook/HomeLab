import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_observer_file_exchange_v1 as exchange
import sa4_observer_signer_v1 as observer


STATEMENT = observer.canonical({
    "schema": "aster-sa4-independent-receipt-proof.v1",
    "receipt_sha256": "1" * 64,
    "observer_id": observer.OBSERVER_ID,
    "observer_key_sha256": observer.KEY_SHA256,
    "signature_algorithm": "rsa-pkcs1v1_5-sha256",
    "authority": "observer-proof-only-no-effect",
})


class SA4ObserverFileExchangeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "exchange"
        self.directory.mkdir(mode=0o700)
        self.patchers = (
            patch.object(exchange, "EXCHANGE_DIR", self.directory),
            patch.object(exchange, "EXPECTED_UID", os.geteuid()),
        )
        for item in self.patchers: item.start(); self.addCleanup(item.stop)

    def response(self, sequence=1, raw=None):
        path = self.directory / f"response-{sequence}.signature"
        path.write_bytes(raw if raw is not None else b"a" * 512 + b"\n")
        path.chmod(0o600)

    def test_exact_response_is_returned_and_request_is_retained(self):
        self.response()
        value = exchange.request_signature(STATEMENT, 1)
        self.assertEqual("a" * 512, value)
        self.assertEqual(STATEMENT,
                         (self.directory / "request-1.json").read_bytes())
        self.assertEqual(0o600, (self.directory / "request-1.json").stat().st_mode & 0o777)

    def test_duplicate_request_fails_closed(self):
        self.response(); exchange.request_signature(STATEMENT, 1)
        with self.assertRaises(FileExistsError):
            exchange.request_signature(STATEMENT, 1)

    def test_bad_response_and_directory_mode_fail_closed(self):
        self.response(raw=b"bad\n")
        with self.assertRaises(ValueError):
            exchange.request_signature(STATEMENT, 1)
        self.directory.chmod(0o755)
        with self.assertRaises(ValueError):
            exchange.request_signature(STATEMENT, 2)

    def test_timeout_retains_request_for_reconciliation(self):
        ticks = iter((0.0, 0.0, 61.0))
        with self.assertRaises(TimeoutError):
            exchange.request_signature(
                STATEMENT, 1, monotonic=lambda: next(ticks), sleep=lambda _: None)
        self.assertTrue((self.directory / "request-1.json").exists())

    def test_response_symlink_is_rejected(self):
        target = self.directory / "target"; target.write_bytes(b"a" * 512 + b"\n")
        target.chmod(0o600)
        (self.directory / "response-1.signature").symlink_to(target)
        with self.assertRaises(OSError):
            exchange.request_signature(STATEMENT, 1)


if __name__ == "__main__":
    unittest.main()
