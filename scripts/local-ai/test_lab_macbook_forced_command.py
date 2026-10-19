import unittest
from unittest import skipUnless
import os
import tempfile
from pathlib import Path

from lab_macbook_forced_command import (ATTESTATION_SECONDS, FORCED_COMMAND,
                                        ForcedCommandConfig, ForcedCommandError,
                                        load_forced_command_config,
                                        create_fresh_session,
                                        write_fresh_attestation)


class LabMacBookForcedCommandTests(unittest.TestCase):
    def config(self):
        return ForcedCommandConfig("jelliott", "SHA256:clientFingerprint=", "a" * 64)

    def env(self):
        return {"SSH_ORIGINAL_COMMAND": FORCED_COMMAND, "SSH_CONNECTION": "192.168.50.12 55222 192.168.50.10 22"}

    def test_fresh_session_binds_sshd_connection_and_expires(self):
        session, expiry = create_fresh_session(self.config(), ssh_env=self.env(), now_epoch=100, nonce="abcdefghijklmnop")
        self.assertEqual(session.principal, "jelliott")
        self.assertEqual(expiry, 100 + ATTESTATION_SECONDS)
        self.assertNotEqual(session.session_id, "abcdefghijklmnop")

    def test_rejects_request_command_or_connection_drift(self):
        for field, value in (("SSH_ORIGINAL_COMMAND", "anything"), ("SSH_CONNECTION", "")):
            with self.subTest(field=field):
                env = {**self.env(), field: value}
                with self.assertRaisesRegex(ForcedCommandError, "SSH"):
                    create_fresh_session(self.config(), ssh_env=env, now_epoch=100, nonce="abcdefghijklmnop")

    def test_rejects_caller_nonce_and_invalid_config(self):
        with self.assertRaisesRegex(ForcedCommandError, "nonce"):
            create_fresh_session(self.config(), ssh_env=self.env(), now_epoch=100, nonce="secret")
        with self.assertRaisesRegex(ForcedCommandError, "configuration"):
            create_fresh_session(ForcedCommandConfig("caller", "SHA256:x=", "a" * 64), ssh_env=self.env(), now_epoch=100, nonce="abcdefghijklmnop")

    def test_rejects_untrusted_config_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text('{"principal":"jelliott","client_key_fingerprint":"SHA256:x=","host_key_sha256":"' + "a" * 64 + '"}')
            with self.assertRaisesRegex(ForcedCommandError, "custody"):
                load_forced_command_config(path)

    def test_rejects_symlinked_config_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            alias = Path(tmp) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ForcedCommandError, "custody"):
                load_forced_command_config(alias / "config.json")

    @skipUnless(os.geteuid() == 0, "root-custody positive test requires root")
    def test_writes_fresh_attestation(self):
        session, _ = create_fresh_session(self.config(), ssh_env=self.env(), now_epoch=100, nonce="abcdefghijklmnop")
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "state"
            parent.mkdir(mode=0o700)
            os.chmod(parent, 0o700)
            path = parent / "session.json"
            write_fresh_attestation(path, session)
            self.assertEqual(path.read_text().count("jelliott"), 1)


if __name__ == "__main__":
    unittest.main()
