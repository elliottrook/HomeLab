import os
from pathlib import Path
import tempfile
import unittest

from handoff import Gateway
from pilot_admission import admit, checksum


class PilotAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        os.chmod(self.root,0o700)
        gateway=Gateway(self.root/'gateway.sqlite','aster-gateway');gateway.close()
        os.chmod(self.root/'gateway.sqlite',0o600)
        self.spec=dict(job_id='orion-connected-20261008',worker='aster-codex-worker-mac',
                       owner='a'*64,request_sha256='b'*64,scope_sha256='c'*64,model='fixture')

    def test_one_admission_persists_and_cannot_be_recreated(self):
        self.assertTrue(admit(self.spec,checksum(self.spec),self.root)['admitted'])
        gateway=Gateway(self.root/'gateway.sqlite','aster-gateway')
        try:
            envelope,state,_=gateway._row(self.spec['job_id'])
            self.assertEqual(state,'queued')
            self.assertEqual(envelope['owner'],self.spec['owner'])
        finally: gateway.close()
        with self.assertRaises(ValueError): admit(self.spec,checksum(self.spec),self.root)

    def test_wrong_approval_or_job_does_not_admit(self):
        with self.assertRaises(ValueError): admit(self.spec,'0'*64,self.root)
        altered=dict(self.spec,job_id='other')
        with self.assertRaises(ValueError): admit(altered,checksum(altered),self.root)
        gateway=Gateway(self.root/'gateway.sqlite','aster-gateway')
        try: self.assertEqual(gateway.list_owned(self.spec['owner']),[])
        finally: gateway.close()

    def test_missing_public_and_linked_ledgers_refused(self):
        ledger=self.root/'gateway.sqlite'
        os.chmod(ledger,0o644)
        with self.assertRaises(ValueError): admit(self.spec,checksum(self.spec),self.root)
        os.chmod(ledger,0o600)
        os.link(ledger,self.root/'alias')
        with self.assertRaises(ValueError): admit(self.spec,checksum(self.spec),self.root)
        ledger.unlink()
        with self.assertRaises(FileNotFoundError): admit(self.spec,checksum(self.spec),self.root)
