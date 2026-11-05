import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import sa3_candidate_j_digest_contract_correction_install as install


class CandidateJDigestContractCorrectionInstallTests(unittest.TestCase):
    def test_exact_change_boundary_and_hashes(self):
        root = Path(__file__).parent
        self.assertEqual(3, len(install.NEW))
        for name in (install.WRAPPER, install.TRANSACTION):
            self.assertEqual(install.NEW[name],
                             hashlib.sha256((root / name).read_bytes()).hexdigest())
        self.assertEqual(2, len(install.EPUB_PINS))

    def test_installed_manifest_derivation_preserves_concurrent_pins(self):
        value = {"schema": "aster-lab-hours-release-manifest.v1",
                 "release": "sa3-candidate-j-runner-source-v14",
                 "pins": {f"pin-{index}": "x" for index in range(37)}}
        value["pins"].update(install.EPUB_PINS)
        value["pins"][install.WRAPPER] = install.OLD[install.WRAPPER]
        value["pins"][install.TRANSACTION] = install.OLD[install.TRANSACTION]
        raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
        expected = install.NEW[install.MANIFEST]
        install.NEW[install.MANIFEST] = hashlib.sha256(
            (json.dumps({**value, "pins": {**value["pins"],
              install.WRAPPER: install.NEW[install.WRAPPER],
              install.TRANSACTION: install.NEW[install.TRANSACTION]}},
              sort_keys=True, indent=2) + "\n").encode()).hexdigest()
        try:
            derived = json.loads(install._derived_manifest(raw))
        finally:
            install.NEW[install.MANIFEST] = expected
        self.assertEqual(41, len(derived["pins"]))
        for name, digest in install.EPUB_PINS.items():
            self.assertEqual(digest, derived["pins"][name])

    def test_cli_is_noop_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                (sys.executable, "-B", install.__file__, "--stage", temporary),
                capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])


if __name__ == "__main__":
    unittest.main()
