import json
import tempfile
import unittest
from pathlib import Path

from build_family_recovery import build
from test_family_recovery import FamilyRecoveryTests
from family_recovery_verify import rehearse


class FamilyRecoveryVerifyTests(unittest.TestCase):
    def test_rehearsal_reconstructs_baseline_and_active(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=FamilyRecoveryTests().fixture(root)
            bundle=root/'bundle'; pin=build(*args,bundle)
            result=rehearse(bundle,root/'rehearsal',pin)
            self.assertTrue(result['passed']); self.assertEqual(result['baseline_skin'],8)
            self.assertGreater(result['addon_files'],10); self.assertEqual(result['external_files'],1)

    def test_wrong_pin_payload_drift_and_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=FamilyRecoveryTests().fixture(root)
            bundle=root/'bundle'; pin=build(*args,bundle)
            with self.assertRaisesRegex(ValueError,'pin'): rehearse(bundle,root/'one','0'*64)
            manifest=json.loads((bundle/'manifest.json').read_text())
            target=bundle/'script.asterruntime'/manifest['addon_files'][0]['path']
            target.write_bytes(b'drift')
            with self.assertRaisesRegex(ValueError,'addon-drift'): rehearse(bundle,root/'two',pin)
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=FamilyRecoveryTests().fixture(root)
            bundle=root/'bundle'; pin=build(*args,bundle); out=root/'out'; out.mkdir()
            with self.assertRaisesRegex(ValueError,'output-exists'): rehearse(bundle,out,pin)


if __name__ == '__main__': unittest.main()
