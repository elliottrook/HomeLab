from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from provision_controller import fingerprint, run
from provision_journal import Journal


class Peer:
    def __init__(self,frames): self.frames=list(frames);self.sent=[];self.closed=False
    def send(self,value): self.sent.append(value)
    def receive(self):
        value=self.frames.pop(0)
        if isinstance(value,Exception): raise value
        return value
    def close(self): self.closed=True


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name).resolve()/'run'
        record={'activated':False,'delivery_confirmed':False,'objects':{'user':'1'}}
        self.identity=Peer([
            ('identity_stage',{'stage':'identity:attempted','record':{'activated':False}}),
            ('identity_stage',{'stage':'identity:confirmed','record':record}),
            ('identity_credentials',{'client_secret':'fixture-private-provider','app_password':'fixture-private-password'}),
            ('identity_done',{'activated':False,'delivery_confirmed':True})])
        self.vault=Peer([
            ('vault_stage',{'stage':'policy:attempted'}),
            ('role_credentials',{'role_id':'fixture-role','secret_id':'fixture-private-secret','secret_id_accessor':'fixture-accessor'}),
            ('admin_revoked',{'confirmed':True}),('vault_done',{'complete':True})])
        self.gateway=Peer([('gateway_done',{'confirmed':True})])
        self.peers={'identity':self.identity,'vault':self.vault,'gateway':self.gateway}

    def tearDown(self): self.tmp.cleanup()

    def execute(self,sink=lambda password,binary:None):
        with patch('provision_controller.subprocess.run'):
            return run(self.path,approved_sha256=fingerprint(),peer_factory=self.peers.__getitem__,keychain_sink=sink)

    def stages(self):
        with sqlite3.connect(self.path/'stages.sqlite') as db:
            return [row[0] for row in db.execute('SELECT stage FROM stages ORDER BY sequence')]

    def test_full_private_handoff_remains_inactive_and_journal_has_no_secrets(self):
        result=self.execute()
        self.assertFalse(result['worker_active']);self.assertFalse(result['delegation_enabled'])
        self.assertEqual(self.stages()[-2:],['admin:revoked','complete'])
        self.assertNotIn(b'fixture-private', (self.path/'stages.sqlite').read_bytes())
        self.assertTrue(all(p.closed for p in self.peers.values()))

    def test_lost_gateway_ack_retains_attempt_without_keychain_or_replay(self):
        self.gateway.frames=[ConnectionError('private response')]
        def forbidden(*args): self.fail('Must not install after lost gateway acknowledgement')
        with self.assertRaises(RuntimeError) as error: self.execute(forbidden)
        self.assertNotIn('private response',str(error.exception))
        self.assertEqual(self.stages()[-2:],['gateway:attempted','incomplete'])
        with self.assertRaises(FileExistsError): self.execute()

    def test_keychain_failure_never_acknowledges_role_delivery(self):
        def failure(*args): raise RuntimeError('private keychain error')
        with self.assertRaises(RuntimeError): self.execute(failure)
        self.assertEqual(self.stages()[-2:],['keychain:attempted','incomplete'])
        self.assertEqual(self.vault.sent[-1],{'accepted':True}) # stage acknowledgement only
        self.assertEqual(len(self.vault.sent),2) # initial request + stage ACK

    def test_forged_early_success_is_rejected(self):
        self.identity.frames=[('identity_done',{'activated':False,'delivery_confirmed':True})]
        with self.assertRaises(RuntimeError): self.execute()
        self.assertEqual(self.stages(),['incomplete'])

    def test_missing_approval_has_no_state(self):
        with self.assertRaises(ValueError): run(self.path)
        self.assertFalse(self.path.exists())

    def test_journal_rejects_secret_shaped_metadata(self):
        journal=Journal(self.path)
        try:
            with self.assertRaises(ValueError): journal.note('identity:confirmed',{'activated':False,'client_secret':'secret'})
            with self.assertRaises(ValueError): journal.note('unknown-secret')
        finally: journal.close()
