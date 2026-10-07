from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from credential_delivery import install


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.destination=Path(self.tmp.name).resolve()/'credential'
        self.packet=dict(role_id='fixture-role',secret_id='fixture-secret',secret_id_accessor='fixture-accessor')

    def tearDown(self): self.tmp.cleanup()

    @staticmethod
    def crypto(operation,data):
        # Test double only; production always invokes systemd-creds.
        if operation=='encrypt': return b'fixture-encrypted:'+data[::-1]
        return data[len(b'fixture-encrypted:'):][::-1]

    def test_disabled_has_no_crypto_or_disk_effect(self):
        with patch('credential_delivery.crypto') as crypto:
            with self.assertRaises(ValueError): install(self.packet,destination=self.destination)
            crypto.assert_not_called()
        self.assertFalse(self.destination.exists())

    def test_encrypted_roundtrip_private_file_and_no_overwrite(self):
        with patch('credential_delivery.crypto',side_effect=self.crypto):
            self.assertTrue(install(self.packet,enabled=True,destination=self.destination))
            self.assertNotIn(b'fixture-secret',self.destination.read_bytes())
            self.assertEqual(self.destination.stat().st_mode & 0o777,0o600)
            with self.assertRaises(ValueError): install(self.packet,enabled=True,destination=self.destination)
        self.assertEqual(len(list(self.destination.parent.iterdir())),1)

    def test_bad_roundtrip_never_publishes(self):
        with patch('credential_delivery.crypto',return_value=b'bad'):
            with self.assertRaises(ValueError): install(self.packet,enabled=True,destination=self.destination)
        self.assertFalse(self.destination.exists())
