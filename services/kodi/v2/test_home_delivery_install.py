import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import home_delivery_install as installer

PUBLIC='ssh-ed25519 '+base64.b64encode(b'\0\0\0\x0bssh-ed25519\0\0\0\x20'+b'X'*32).decode()

class InstallTests(unittest.TestCase):
    def test_restricts_only_owned_key_and_revocation_preserves_owner_keys(self):
        original=b'ssh-ed25519 first-owner\nssh-ed25519 second-owner\n'
        line=installer.key_line(PUBLIC)
        for option in (b'restrict,',b'from="192.168.20.11"',b'command="/usr/bin/python3 /storage/.aster-home-delivery/receive.py"'):
            self.assertIn(option,line)
        enabled=installer.transform(original,line,True)
        self.assertEqual(installer.transform(enabled,line,False),original)
        self.assertEqual(installer.transform(enabled,line,True),enabled)
        later=enabled+b'ssh-ed25519 later-owner\n'
        self.assertEqual(installer.transform(later,line,False),original+b'ssh-ed25519 later-owner\n')

    def test_duplicate_or_unrestricted_credential_refused(self):
        line=installer.key_line(PUBLIC)
        with self.assertRaisesRegex(RuntimeError,'unrestricted'):
            installer.transform((PUBLIC+'\n').encode(),line,True)
        with self.assertRaises(RuntimeError):installer.transform(line+line,line,False)

    def test_private_checkpoint_install_enable_disable_cycle(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);stage=base/'stage';stage.mkdir();keys=base/'authorized_keys';keys.write_bytes(b'owner-one\nowner-two\n');keys.chmod(0o600)
            files={}
            for name in ('receive.py','home_status_model.py'):
                (stage/name).write_bytes(name.encode());files[name]=hashlib.sha256(name.encode()).hexdigest()
            (stage/'manifest.json').write_text(json.dumps(dict(kind='hp-home-delivery-v1',files=files)))
            pin=hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest();original=keys.read_bytes()
            with patch.multiple(installer,ROOT=base/'installed',CP=base/'checkpoint',KEYS=keys,ORIGINAL=hashlib.sha256(original).hexdigest()):
                self.assertTrue(installer.run('prepare',stage,pin,PUBLIC)['passed'])
                self.assertTrue(installer.run('enable',stage,pin,PUBLIC)['restricted_key_enabled'])
                self.assertFalse(installer.run('disable',stage,pin,PUBLIC)['restricted_key_enabled'])
                self.assertEqual(keys.read_bytes(),original)

if __name__=='__main__':unittest.main()
