import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import sa4_observer_file_exchange_v1 as exchange
import sa4_observer_signer_v1 as observer
import sa4_proxmox_observer_bridge_v1 as bridge


STATEMENT = observer.canonical({
    "schema": "aster-sa4-independent-receipt-proof.v1",
    "receipt_sha256": "2" * 64,
    "observer_id": observer.OBSERVER_ID,
    "observer_key_sha256": observer.KEY_SHA256,
    "signature_algorithm": "rsa-pkcs1v1_5-sha256",
    "authority": "observer-proof-only-no-effect",
})


class SA4ObserverExchangeJoinedTests(unittest.TestCase):
    def test_fixed_bridge_completes_blocked_LXC_exchange(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); lxc = root / "lxc"; host = root / "host"
            lxc.mkdir(mode=0o700); host.mkdir(mode=0o700)
            result = []; failure = []
            def requester():
                try:
                    result.append(exchange.request_signature(STATEMENT, 1))
                except BaseException as error:
                    failure.append(error)
            def runner(arguments, **kwargs):
                if arguments[1] == "pull":
                    shutil.copyfile(lxc / "request-1.json", Path(arguments[4]))
                    Path(arguments[4]).chmod(0o600)
                else:
                    shutil.copyfile(Path(arguments[3]),
                                    lxc / "response-1.signature")
                    (lxc / "response-1.signature").chmod(0o600)
                return subprocess.CompletedProcess(arguments, 0, b"", b"")
            with patch.object(exchange, "EXCHANGE_DIR", lxc), \
                 patch.object(exchange, "EXPECTED_UID", os.geteuid()), \
                 patch.object(bridge, "BRIDGE_DIRECTORY", host), \
                 patch.object(bridge, "EXPECTED_UID", os.geteuid()):
                thread = threading.Thread(target=requester); thread.start()
                for _ in range(100):
                    if (lxc / "request-1.json").exists(): break
                    time.sleep(0.001)
                bridge.bridge(1, runner=runner, signer=lambda _raw: "b" * 512)
                thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual([], failure)
            self.assertEqual(["b" * 512], result)
            self.assertEqual(STATEMENT, (host / "request-1.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
