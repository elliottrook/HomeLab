import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

import launch_d4_candidate_h as launcher


class CandidateHLauncherTests(unittest.TestCase):
    def test_frozen_hashes_match_candidate_manifest(self):
        root = Path(__file__).parents[2] / "services/aster-agent/evals"
        manifest = json.loads(
            (root / "sa3-development-attempt-11-source-manifest.json").read_text()
        )
        expected = {
            row["name"]: (row["bytes"], row["sha256"])
            for row in manifest["files"]
        }
        self.assertEqual(expected, launcher.FILES)
        self.assertEqual(manifest["run_digest"], launcher.RUN_DIGEST)

    def test_packet_validation_requires_exact_private_regular_files(self):
        uid, gid = os.getuid(), os.getgid()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "packet"
            root.mkdir(mode=0o700)
            for name, (size, digest) in launcher.FILES.items():
                path = root / name
                path.write_bytes(b"x" * size)
                path.chmod(0o600)
                launcher.FILES[name] = (size, hashlib.sha256(path.read_bytes()).hexdigest())
            try:
                launcher.validate_packet(root, uid=uid, gid=gid)
                (root / next(iter(launcher.FILES))).chmod(0o644)
                with self.assertRaisesRegex(ValueError, "custody mismatch"):
                    launcher.validate_packet(root, uid=uid, gid=gid)
            finally:
                launcher.FILES.clear()
                launcher.FILES.update({
                    row["name"]: (row["bytes"], row["sha256"])
                    for row in json.loads(
                        (Path(__file__).parents[2] / "services/aster-agent/evals/"
                         "sa3-development-attempt-11-source-manifest.json").read_text()
                    )["files"]
                })

    def test_key_parser_accepts_one_fictional_value_and_rejects_ambiguity(self):
        uid, gid = os.getuid(), os.getgid()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aster.env"
            path.write_bytes(b"OTHER=value\nASTER_LLAMA_API_KEY='fictional-key'\n")
            path.chmod(0o640)
            secret = launcher.read_key_bytes(path, uid=uid, gid=gid)
            self.assertEqual(secret, bytearray(b"fictional-key"))
            path.write_bytes(
                b"ASTER_LLAMA_API_KEY=one\nASTER_LLAMA_API_KEY=two\n"
            )
            with self.assertRaisesRegex(ValueError, "exactly one"):
                launcher.read_key_bytes(path, uid=uid, gid=gid)

    def test_pipe_delivery_clears_secret_and_excludes_environment_key(self):
        secret = bytearray(b"fictional-key")
        child = (
            "import os,sys; "
            "fd=int(sys.argv[-1]); "
            "value=os.read(fd,4097); "
            "raise SystemExit(0 if value==b'fictional-key' "
            "and 'ASTER_LLAMA_API_KEY' not in os.environ else 9)"
        )
        old_root = launcher.PACKET_DIR
        try:
            launcher.PACKET_DIR = Path("/")
            result = launcher.run_with_key_fd(
                [sys.executable, "-c", child], secret, timeout=5
            )
        finally:
            launcher.PACKET_DIR = old_root
        self.assertEqual(result, 0)
        self.assertEqual(secret, bytearray(len(secret)))


if __name__ == "__main__":
    unittest.main()
