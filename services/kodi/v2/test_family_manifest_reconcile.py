import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from family_manifest_reconcile import build, digest, encoded
from family_manifest_reconcile_install import run


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)


def fixture(root):
    storage = root/'storage'; addon = storage/'.kodi/addons/script.asterruntime'
    skin = storage/'.kodi/addons/skin.asterhome'; component = addon/'series'
    component.mkdir(parents=True); write(component/'manifest.json', b'{}')
    home = b'<window id="0"><controls/></window>'
    other = b'<window id="1"><controls/></window>'
    write(skin/'1080i/Home.xml', home); write(skin/'1080i/Other.xml', other)
    family = dict(schema=1, kind='aster-family-runtime.v1',
        components={'series': {'manifest_sha256': digest(b'{}'), 'files': 0}},
        skin={'1080i/Home.xml': '0'*64, '1080i/Other.xml': digest(other)})
    write(addon/'family-manifest.json', encoded(family))
    return storage, addon, skin


class FamilyManifestReconcileTests(unittest.TestCase):
    def test_exact_drift_build_install_verify_and_rollback(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent); storage, addon, skin = fixture(root); stage = root/'stage'
            before = hashlib.sha256((addon/'family-manifest.json').read_bytes()).hexdigest()
            pin = build(addon, skin, stage)
            result = run('install', stage, storage, pin, idle=lambda: True)
            self.assertTrue(result['references_verified'])
            self.assertTrue(run('verify', stage, storage, pin, idle=lambda: True)['active'])
            self.assertTrue(run('rollback', stage, storage, pin, idle=lambda: True)['rolled_back'])
            self.assertEqual(hashlib.sha256((addon/'family-manifest.json').read_bytes()).hexdigest(), before)

    def test_extra_drift_refuses_before_output(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent); _, addon, skin = fixture(root)
            (skin/'1080i/Other.xml').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'unexpected-drift'):
                build(addon, skin, root/'stage')
            self.assertFalse((root/'stage').exists())

    def test_live_predecessor_drift_refuses_before_checkpoint(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent); storage, addon, skin = fixture(root); stage = root/'stage'
            pin = build(addon, skin, stage)
            (addon/'family-manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'predecessor-drift'):
                run('install', stage, storage, pin, idle=lambda: True)
            self.assertFalse((storage/'.aster-checkpoints/aster-family-manifest1').exists())


if __name__ == '__main__': unittest.main()
