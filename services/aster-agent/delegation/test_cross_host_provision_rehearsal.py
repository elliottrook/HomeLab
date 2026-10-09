from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import cross_host_provision_rehearsal as rehearsal
from provision_controller import Pipe


class CrossHostHarnessTests(unittest.TestCase):
    def test_all_three_cases_over_local_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            def peer(kind,case):
                return Pipe([sys.executable,'-B',str(Path(__file__).with_name('fixture_provision_peer.py')),
                    '--fictional-only','--kind',kind,'--receipt',str(root/(case+'.receipt')),
                    '--scenario','gateway-disconnect' if case=='gateway-disconnect' else 'success'])
            def receipt(case):
                self.assertEqual((root/(case+'.receipt')).read_text(),'fictional-admin-revoked')
            with patch.object(rehearsal,'peer',side_effect=peer),patch.object(rehearsal,'receipt',side_effect=receipt):
                result=rehearsal.run(root/'run',rehearsal.fingerprint())
            self.assertTrue(result['passed']);self.assertEqual(len(result['cases']),3)
            self.assertFalse(result['keychain_accessed'])

    def test_no_approval_creates_no_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary).resolve()/'absent'
            with self.assertRaises(ValueError): rehearsal.run(path,None)
            self.assertFalse(path.exists())
