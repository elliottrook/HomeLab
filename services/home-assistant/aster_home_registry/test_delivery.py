import asyncio
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

BASE=Path(__file__).parent
SPEC=importlib.util.spec_from_file_location('delivery_test_module',BASE/'custom_components/aster_home_registry/delivery.py')
delivery=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(delivery)

class DeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder=tempfile.TemporaryDirectory();self.root=Path(self.folder.name)
        self.raw=json.dumps(dict(schema_version=4,snapshot_id='ha-home-dashboard-v4',observed_at=datetime.now(timezone.utc).isoformat(),entities=[])).encode()
        self.report=self.root/'dashboard.json';self.report.write_bytes(self.raw);self.report.chmod(0o600)
        for name,raw in (('id_ed25519',b'synthetic-not-a-real-key'),('known_hosts',b'pinned-public-hostkey'),
                         ('home_status_model.py',(BASE.parents[1]/'kodi/v2/home_status_model.py').read_bytes())):
            (self.root/name).write_bytes(raw);(self.root/name).chmod(0o600)
        (self.root/'identity.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256((self.root/'home_status_model.py').read_bytes()).hexdigest(),
            hostkey_sha256=hashlib.sha256((self.root/'known_hosts').read_bytes()).hexdigest(),public_fingerprint='synthetic-public-fingerprint')))
        (self.root/'identity.json').chmod(0o600)
        (self.root/'enabled.json').write_text(json.dumps(dict(enabled=True,interval_seconds=300,target='hp-only')));(self.root/'enabled.json').chmod(0o600)
        self.patch=patch.multiple(delivery,ROOT=self.root,REPORT=self.report,_lock=asyncio.Lock());self.patch.start()
        self.calls=[]
    async def asyncTearDown(self):self.patch.stop();self.folder.cleanup()
    def transport(self,*,denied=False):
        test=self
        class Connection:
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            async def run(self,command,**kwargs):
                test.calls.append((command,kwargs))
                if denied:raise RuntimeError('secret-and-private-data-must-not-be-logged')
                raw=kwargs['input'];payload=json.loads(raw)
                return types.SimpleNamespace(exit_status=0,stdout=json.dumps(dict(ok=True,sha256=hashlib.sha256(raw).hexdigest(),source_at=payload['observed_at'])).encode())
        def connect(host,**kwargs):
            test.calls.append((host,kwargs));return Connection()
        return types.SimpleNamespace(connect=connect)

    async def test_pins_host_and_identity_no_agent_config_or_password(self):
        with patch.dict(sys.modules,{'asyncssh':self.transport()}):result=await delivery.publish()
        self.assertTrue(result['ok']);host,options=self.calls[0]
        self.assertEqual(host,'192.168.1.140');self.assertEqual(options['known_hosts'],str(self.root/'known_hosts'))
        self.assertEqual(options['client_keys'],[str(self.root/'id_ed25519')]);self.assertEqual(options['preferred_auth'],['publickey'])
        self.assertEqual(options['config'],[]);self.assertIsNone(options['agent_path']);self.assertTrue(options['disable_trivial_auth'])
        self.assertEqual(self.calls[1][0],'aster-home-publish-v1')
        self.assertEqual((self.root/'health.json').stat().st_mode&0o777,0o600)

    async def test_disabled_never_contacts_network_or_reads_key(self):
        (self.root/'enabled.json').unlink();(self.root/'id_ed25519').unlink()
        with patch.dict(sys.modules,{'asyncssh':self.transport()}):result=await delivery.publish()
        self.assertEqual(result['code'],'disabled');self.assertEqual(self.calls,[])

    async def test_failure_retains_last_success_without_secret_exception(self):
        with patch.dict(sys.modules,{'asyncssh':self.transport()}):await delivery.publish()
        first=json.loads((self.root/'health.json').read_text())
        with patch.dict(sys.modules,{'asyncssh':self.transport(denied=True)}):result=await delivery.publish()
        status=(self.root/'health.json').read_text();self.assertFalse(result['ok'])
        self.assertEqual(json.loads(status)['last_success_at'],first['last_success_at']);self.assertNotIn('secret-and-private',status)

    async def test_modified_host_pin_fails_before_network(self):
        (self.root/'known_hosts').write_bytes(b'changed-key')
        with patch.dict(sys.modules,{'asyncssh':self.transport()}):result=await delivery.publish()
        self.assertFalse(result['ok']);self.assertEqual(self.calls,[])

    async def test_overlap_does_not_start_second_connection(self):
        async with delivery._lock:
            with patch.dict(sys.modules,{'asyncssh':self.transport()}):result=await delivery.publish()
        self.assertEqual(result['code'],'busy');self.assertEqual(self.calls,[])

if __name__=='__main__':unittest.main()
