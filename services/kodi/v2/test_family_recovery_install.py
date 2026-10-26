import json
import tempfile
import unittest
from pathlib import Path

from build_family_recovery import build
from family_recovery_install import run
from test_family_recovery import FamilyRecoveryTests


def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(source.read_bytes())


class FamilyRecoveryInstallTests(unittest.TestCase):
    def test_adopt_verify_rollback_install(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=FamilyRecoveryTests().fixture(root)
            bundle=root/'bundle'; pin=build(*args,bundle); value=json.loads((bundle/'manifest.json').read_text())
            storage=root/'storage'
            for row in value['addon_files']: copy(bundle/'script.asterruntime'/row['path'],storage/'.kodi/addons/script.asterruntime'/row['path'])
            for row in value['skin']: copy(bundle/'skin'/row['path'],storage/'.kodi/addons/skin.asterhome'/row['path'])
            copy(bundle/'external/player.py',storage/value['external'][0]['path'])
            self.assertTrue(run('adopt',bundle,storage,pin,idle=lambda:True)['adopted'])
            self.assertTrue(run('verify',bundle,storage,pin,idle=lambda:True)['active'])
            self.assertTrue(run('rollback',bundle,storage,pin,idle=lambda:True)['rolled_back'])
            self.assertFalse(run('verify',bundle,storage,pin,idle=lambda:True)['active'])
            self.assertTrue(run('install',bundle,storage,pin,idle=lambda:True)['installed'])
            self.assertTrue(run('verify',bundle,storage,pin,idle=lambda:True)['active'])

    def test_busy_wrong_pin_and_drift_refused(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=FamilyRecoveryTests().fixture(root)
            bundle=root/'bundle'; pin=build(*args,bundle)
            with self.assertRaisesRegex(ValueError,'home-idle'): run('adopt',bundle,root/'s',pin,idle=lambda:False)
            with self.assertRaisesRegex(ValueError,'pin'): run('adopt',bundle,root/'s','0'*64,idle=lambda:True)


if __name__=='__main__': unittest.main()
