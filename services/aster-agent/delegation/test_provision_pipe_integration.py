from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from provision_controller import Pipe,run,fingerprint


class PipeIntegrationTests(unittest.TestCase):
    def execute(self,scenario='success',keychain_failure=False):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();receipt=root/'revocation-receipt'
            peers=[];delivered=[]
            def factory(kind):
                peer=Pipe([sys.executable,'-B',str(Path(__file__).with_name('fixture_provision_peer.py')),
                    '--fictional-only','--kind',kind,'--receipt',str(receipt),'--scenario',scenario])
                peers.append(peer);return peer
            def sink(password,binary):
                if keychain_failure: raise ValueError('fictional-private-error')
                self.assertEqual(password,'fictional-password');delivered.append(True)
            with patch('provision_controller.subprocess.run'): # compiler only; no Keychain access
                if scenario!='success' or keychain_failure:
                    with self.assertRaisesRegex(RuntimeError,'Provisioning incomplete'):
                        run(root/'journal',approved_sha256=fingerprint(),peer_factory=factory,keychain_sink=sink)
                    complete=False
                else:
                    result=run(root/'journal',approved_sha256=fingerprint(),peer_factory=factory,keychain_sink=sink)
                    self.assertFalse(result['worker_active']);self.assertFalse(result['delegation_enabled'])
                    complete=result['complete']
            self.assertTrue(receipt.exists(),'Vault peer must revoke on disconnected controller too')
            self.assertTrue(all(peer.process.poll() is not None for peer in peers))
            with sqlite3.connect(root/'journal/stages.sqlite') as db:
                stages=[row[0] for row in db.execute('SELECT stage FROM stages ORDER BY sequence')]
            self.assertEqual(stages[-1],'complete' if complete else 'incomplete')
            self.assertNotIn(b'fictional-password',(root/'journal/stages.sqlite').read_bytes())
            self.assertNotIn(b'fictional-secret',(root/'journal/stages.sqlite').read_bytes())
            if scenario!='success' or keychain_failure: self.assertFalse(delivered)

    def test_complete_owned_pipe_chain(self): self.execute()
    def test_gateway_disconnect_revokes_without_keychain_or_replay(self): self.execute('gateway-disconnect')
    def test_keychain_failure_revokes_and_stops(self): self.execute(keychain_failure=True)
