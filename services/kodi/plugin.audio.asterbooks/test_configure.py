"""Credential-free checks for the interactive Mac configuration helper."""

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from configure_client import SERVER_URL, create_config


class ConfigureTests(unittest.TestCase):
    def test_private_config_is_created_once_and_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            profile = Path(temp) / 'plugin.audio.asterbooks'
            destination = create_config(profile, 's' * 32)
            self.assertEqual(json.loads(destination.read_text()),
                             {'server_url': SERVER_URL, 'api_key': 's' * 32})
            self.assertEqual(stat.S_IMODE(profile.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                create_config(profile, 't' * 32)
            self.assertEqual(json.loads(destination.read_text())['api_key'], 's' * 32)

    def test_invalid_key_removes_only_new_config(self):
        with tempfile.TemporaryDirectory() as temp:
            profile = Path(temp) / 'plugin.audio.asterbooks'
            with self.assertRaises(Exception):
                create_config(profile, 'short')
            self.assertFalse((profile / 'client.json').exists())

    def test_linked_profile_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real_profile = root / 'real'
            real_profile.mkdir()
            link = root / 'linked'
            os.symlink(real_profile, link)
            with self.assertRaises(Exception):
                create_config(link, 's' * 32)
            self.assertFalse((real_profile / 'client.json').exists())


if __name__ == '__main__':
    unittest.main()
