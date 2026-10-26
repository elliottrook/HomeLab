import tempfile
from pathlib import Path
import unittest

from build_seerr_ui_patch import build
from seerr_ui_patch_install import run


class SeerrUIPatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.temporary.name)
        self.stage = self.root / 'stage'
        self.pin = build(self.stage)
        self.storage = self.root / 'storage'
        manifest = __import__('json').loads((self.stage / 'manifest.json').read_text())
        base = self.storage / '.aster-checkpoints/aster-seerr-page1/manifest.json'
        base.parent.mkdir(parents=True)
        base.write_bytes(b'parent')
        manifest['parent_manifest_sha256'] = __import__('hashlib').sha256(b'parent').hexdigest()
        raw = __import__('json').dumps(manifest, indent=2, sort_keys=True).encode() + b'\n'
        (self.stage / 'manifest.json').write_bytes(raw)
        self.pin = __import__('hashlib').sha256(raw).hexdigest()
        for row in manifest['files']:
            target = self.storage / '.kodi/addons/script.asterseerr' / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            # Tests patch the manifest's predecessor to isolated fixture bytes.
            target.write_bytes(('old-' + row['path']).encode())
            row['before_sha256'] = __import__('hashlib').sha256(target.read_bytes()).hexdigest()
        raw = __import__('json').dumps(manifest, indent=2, sort_keys=True).encode() + b'\n'
        (self.stage / 'manifest.json').write_bytes(raw)
        self.pin = __import__('hashlib').sha256(raw).hexdigest()

    def tearDown(self):
        self.temporary.cleanup()

    def test_install_verify_and_rollback(self):
        result = run('install', self.stage, self.storage, self.pin,
                     stopped=lambda: True)
        self.assertTrue(result['checkpoint_verified'])
        self.assertTrue(run('verify', self.stage, self.storage, self.pin,
                            stopped=lambda: False)['active'])
        run('rollback', self.stage, self.storage, self.pin, stopped=lambda: True)
        self.assertFalse(run('verify', self.stage, self.storage, self.pin,
                             stopped=lambda: False)['active'])

    def test_install_requires_stopped_kodi_and_exact_predecessor(self):
        with self.assertRaisesRegex(ValueError, 'stop-kodi-first'):
            run('install', self.stage, self.storage, self.pin, stopped=lambda: False)
        target = self.storage / '.kodi/addons/script.asterseerr/default.py'
        target.write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'active-drift'):
            run('install', self.stage, self.storage, self.pin, stopped=lambda: True)


if __name__ == '__main__':
    unittest.main()
