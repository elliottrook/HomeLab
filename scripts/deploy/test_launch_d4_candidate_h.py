import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

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
            root.mkdir(mode=0o750)
            for name, (size, digest) in launcher.FILES.items():
                path = root / name
                path.write_bytes(b"x" * size)
                path.chmod(0o640)
                launcher.FILES[name] = (size, hashlib.sha256(path.read_bytes()).hexdigest())
            try:
                launcher.validate_packet(root, uid=uid, gid=gid)
                (root / next(iter(launcher.FILES))).chmod(0o600)
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
                [sys.executable, "-c", child], secret, timeout=5,
                child_uid=None, child_gid=None,
            )
        finally:
            launcher.PACKET_DIR = old_root
        self.assertEqual(result, 0)
        self.assertEqual(secret, bytearray(len(secret)))

    def test_output_directory_is_separate_empty_and_private(self):
        uid, gid = os.getuid(), os.getgid()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "output"
            root.mkdir(mode=0o700)
            launcher.validate_output_directory(root, uid=uid, gid=gid)
            (root / "unexpected").write_text("x")
            with self.assertRaisesRegex(ValueError, "must be empty"):
                launcher.validate_output_directory(root, uid=uid, gid=gid)

    def test_fixed_identity_has_no_supplementary_access(self):
        config = (
            Path(__file__).parents[2] / "services/aster-agent/systemd/"
            "aster-d4-eval.sysusers.conf"
        ).read_text().strip()
        self.assertEqual(
            config,
            'u aster-d4-eval 977 "Aster D4 evaluation runner" '
            '/nonexistent /usr/sbin/nologin',
        )
        self.assertEqual(launcher.EVAL_UID, 977)
        self.assertEqual(launcher.EVAL_GID, 977)
        self.assertNotIn("aster ", config)

    def test_identity_validation_rejects_supplementary_groups(self):
        account = mock.Mock(
            pw_uid=977, pw_gid=977, pw_shell="/usr/sbin/nologin"
        )
        group = mock.Mock(gr_gid=977)
        with mock.patch.object(launcher.pwd, "getpwnam", return_value=account), \
             mock.patch.object(launcher.grp, "getgrnam", return_value=group), \
             mock.patch.object(
                 launcher.os, "getgrouplist", return_value=[977, 1000]
             ):
            with self.assertRaisesRegex(ValueError, "supplementary groups"):
                launcher.validate_eval_identity()

    def test_production_spawn_drops_to_fixed_identity_and_clears_groups(self):
        secret = bytearray(b"fictional-key")
        process = mock.Mock()
        process.wait.return_value = 0
        old_root = launcher.PACKET_DIR
        try:
            launcher.PACKET_DIR = Path("/")
            with mock.patch.object(launcher.subprocess, "Popen", return_value=process) as popen:
                result = launcher.run_with_key_fd(
                    ["/fixed/python", "/fixed/runner"], secret, timeout=5
                )
        finally:
            launcher.PACKET_DIR = old_root
        self.assertEqual(result, 0)
        kwargs = popen.call_args.kwargs
        self.assertEqual(kwargs["user"], 977)
        self.assertEqual(kwargs["group"], 977)
        self.assertEqual(kwargs["extra_groups"], ())
        self.assertEqual(kwargs["umask"], 0o077)
        self.assertTrue(kwargs["start_new_session"])
        self.assertNotIn("ASTER_LLAMA_API_KEY", kwargs["env"])
        self.assertEqual(secret, bytearray(len(secret)))

    def test_oneshot_unit_is_bounded_and_not_installable(self):
        unit = (
            Path(__file__).parents[2] / "services/aster-agent/systemd/"
            "aster-d4-candidate-h.service"
        ).read_text()
        self.assertIn("Type=oneshot", unit)
        self.assertIn("NoNewPrivileges=yes", unit)
        self.assertIn("CapabilityBoundingSet=CAP_SETUID CAP_SETGID", unit)
        self.assertIn("ReadOnlyPaths=/etc/aster/aster.env /var/lib/aster/d4-candidate-h", unit)
        self.assertIn("ReadWritePaths=/var/lib/aster/d4-candidate-h-output", unit)
        self.assertIn("RuntimeMaxSec=2250", unit)
        self.assertIn("KillMode=control-group", unit)
        self.assertNotIn("[Install]", unit)


if __name__ == "__main__":
    unittest.main()
