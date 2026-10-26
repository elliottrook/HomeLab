from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import home_delivery_receiver as receiver
import home_status_model as model

NOW=datetime(2026,10,26,7,tzinfo=timezone.utc)
def report(time):return json.dumps(dict(schema_version=4,snapshot_id='ha-home-dashboard-v4',observed_at=time.isoformat(),entities=[dict(id='light.room',name='Room',kind='light',availability='available',state='on')])).encode()

class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.cp=self.root/'cp';self.cp.mkdir(mode=0o700)
        self.feed=self.root/'feed.json';self.before=report(NOW-timedelta(minutes=5));self.feed.write_bytes(self.before)
        self.feed.chmod(0o600)
        self.pin=hashlib.sha256(self.before).hexdigest()
        receiver.write_json(self.cp/'publication.json',dict(feed_sha256=self.pin,manifest_sha256=receiver.MANIFEST))
    def tearDown(self):self.tmp.cleanup()
    def run_receive(self,raw):return receiver.receive(raw,model,now=NOW,feed=self.feed,checkpoint=self.cp)

    def test_updates_only_display_and_private_recovery_files(self):
        result=self.run_receive(report(NOW));self.assertTrue(result['ok']);self.assertTrue(result['changed'])
        self.assertEqual((self.cp/'delivery-previous.json').read_bytes(),self.before)
        self.assertEqual(self.feed.stat().st_mode&0o777,0o600)
        self.assertEqual(self.run_receive(report(NOW))['changed'],False)

    def test_stale_future_malformed_and_older_refused(self):
        for raw in (b'bad',b'X'*262145,report(NOW-timedelta(minutes=11)),report(NOW+timedelta(seconds=11)),report(NOW-timedelta(minutes=6))):
            with self.assertRaises(RuntimeError):self.run_receive(raw)
            self.assertEqual(self.feed.read_bytes(),self.before)

    def test_conflicting_same_timestamp_refused(self):
        value=json.loads(self.before);value['entities'][0]['state']='off'
        with self.assertRaisesRegex(RuntimeError,'same-time'):self.run_receive(json.dumps(value).encode())

    def test_external_file_drift_and_symlink_refused(self):
        self.feed.write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError,'drift'):self.run_receive(report(NOW))
        self.feed.unlink();self.feed.symlink_to(self.cp/'publication.json')
        with self.assertRaisesRegex(RuntimeError,'private-path'):self.run_receive(report(NOW))

    def test_interrupted_publish_recovers_only_owned_generation(self):
        new=report(NOW);pin=hashlib.sha256(new).hexdigest()
        receiver.write_json(self.cp/'delivery-pending.json',dict(before=self.pin,after=pin,source_at=NOW.isoformat(),status='pending'))
        self.feed.write_bytes(new)
        result=self.run_receive(new);self.assertFalse(result['changed'])
        self.assertEqual(json.loads((self.cp/'publication.json').read_text())['feed_sha256'],pin)

    def test_prewrite_interrupt_and_ambiguous_write(self):
        new=report(NOW);pin=hashlib.sha256(new).hexdigest()
        receiver.write_json(self.cp/'delivery-pending.json',dict(before=self.pin,after=pin,source_at=NOW.isoformat(),status='pending'))
        self.assertTrue(self.run_receive(new)['ok'])
        receiver.write_json(self.cp/'delivery-pending.json',dict(before='not-owned',after='also-not-owned',source_at=NOW.isoformat(),status='pending'))
        with self.assertRaisesRegex(RuntimeError,'uncertain'):self.run_receive(new)

    def test_normal_command_is_not_a_shell(self):
        with patch.dict('os.environ',dict(SSH_ORIGINAL_COMMAND='id',SSH_CONNECTION='192.168.20.11 1234 192.168.1.140 22'),clear=True),patch('sys.argv',['receive.py']):
            self.assertEqual(receiver.main(),1)

    def test_other_source_and_subsystem_denied_before_files(self):
        for command,source in (('aster-home-publish-v1','192.168.1.157'),('internal-sftp','192.168.20.11')):
            with patch.dict('os.environ',dict(SSH_ORIGINAL_COMMAND=command,SSH_CONNECTION=source+' 1234 192.168.1.140 22'),clear=True),patch('sys.argv',['receive.py']),patch.object(receiver,'secure') as secure:
                self.assertEqual(receiver.main(),1);secure.assert_not_called()

if __name__=='__main__':unittest.main()
