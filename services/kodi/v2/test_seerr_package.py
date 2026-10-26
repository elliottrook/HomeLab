import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_seerr_page import build
from seerr_install import inspect, run, verify_active


HOME = '''<window><controls>
<control type="group" id="23"><control type="button" id="130"><label>Old</label></control></control>
<control type="group" id="22"><control type="label"><label>Rows stay</label></control></control>
</controls></window>'''


class SeerrPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.temporary.name)
        self.home = self.root / 'Home.xml'
        self.home.write_text(HOME)
        self.stage = self.root / 'aster-seerr-page1'
        self.pin = build(self.home, self.stage)

    def tearDown(self):
        self.temporary.cleanup()

    def storage(self):
        storage = self.root / 'storage'
        target = storage / '.kodi/addons/skin.asterhome/1080i/Home.xml'
        target.parent.mkdir(parents=True)
        target.write_text(HOME)
        return storage

    def test_candidate_is_pinned_and_contains_no_seerr_credential(self):
        manifest = inspect(self.stage, self.pin)
        self.assertEqual(manifest['kind'], 'hp-seerr-page.v1')
        combined = b''.join(path.read_bytes() for path in self.stage.rglob('*') if path.is_file())
        self.assertNotIn(b':5055', combined)
        self.assertNotIn(b'SEERR_PASSWORD', combined)
        self.assertIn(b'http://192.168.20.40:8788', combined)
        self.assertIn(b'RunScript(script.asterseerr)',
                      (self.stage / 'skin/1080i/Home.xml').read_bytes())

    def test_install_verify_and_rollback_preserve_exact_predecessor(self):
        storage = self.storage()
        result = run('install', self.stage, storage, self.pin, idle=lambda: True)
        self.assertTrue(result['checkpoint_verified'])
        self.assertTrue(verify_active(self.stage, storage, self.pin))
        self.assertTrue((storage / '.kodi/addons/script.asterseerr/default.py').is_file())
        self.assertTrue((storage / '.kodi/addons/skin.asterhome/1080i/custom_1132_requests.xml').is_file())
        run('rollback', self.stage, storage, self.pin, idle=lambda: True)
        self.assertFalse(verify_active(self.stage, storage, self.pin))
        self.assertEqual((storage / '.kodi/addons/skin.asterhome/1080i/Home.xml').read_text(), HOME)
        self.assertFalse((storage / '.kodi/addons/skin.asterhome/1080i/custom_1132_requests.xml').exists())

    def test_wrong_predecessor_and_manifest_tamper_fail_closed(self):
        storage = self.storage()
        (storage / '.kodi/addons/skin.asterhome/1080i/Home.xml').write_text(HOME + '\nchanged')
        with self.assertRaisesRegex(ValueError, 'seerr-install-exact-predecessor'):
            run('install', self.stage, storage, self.pin, idle=lambda: True)
        payload = self.stage / 'script.asterseerr/default.py'
        payload.write_bytes(payload.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'seerr-install-addon-drift'):
            inspect(self.stage, self.pin)

    def test_build_is_immutable(self):
        with self.assertRaisesRegex(ValueError, 'seerr-build-path'):
            build(self.home, self.stage)
        actual = hashlib.sha256((self.stage / 'manifest.json').read_bytes()).hexdigest()
        self.assertEqual(actual, self.pin)


if __name__ == '__main__':
    unittest.main()
