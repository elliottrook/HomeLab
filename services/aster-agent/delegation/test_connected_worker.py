import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connected_worker import connected_manifest, execute, main


class ConnectedWorkerTests(unittest.IsolatedAsyncioTestCase):
    def test_default_starts_nothing(self):
        output=io.StringIO()
        with patch('sys.argv',['connected_worker']), patch('connected_worker.ConfigClient') as client, \
                patch('connected_worker.WorkerToken') as credentials, contextlib.redirect_stdout(output):
            main()
        self.assertFalse(json.loads(output.getvalue())['enabled'])
        client.assert_not_called(); credentials.assert_not_called()

    def test_manifest_binds_assignment_payload_model_and_sources(self):
        value=connected_manifest({'model':'fixture','reasoning_effort':'medium'},'job')
        self.assertEqual(value['maximum_model_turns'],1)
        self.assertFalse(value['automatic_retry'])
        self.assertIn('credentials.py',value['source_hashes'])
        self.assertIn('connected_worker.py',value['source_hashes'])
        with self.assertRaises(ValueError): connected_manifest({'model':'fixture'},'../job')

    async def test_execution_uses_fixed_payload_and_private_evidence(self):
        from pilot import FIXTURE
        prepared=connected_manifest({'model':'fixture','reasoning_effort':'medium'},'job')
        async def run(worker,inbox,store,agent,job,payload,**kwargs):
            self.assertEqual(job,'job'); self.assertEqual(payload,FIXTURE.encode())
            self.assertTrue(kwargs['enabled'])
            return {'state':'completed','answer':'do not persist here'}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'run'
            with patch('connected_worker.PipeAgent'), patch('connected_worker.WorkerToken') as credential, \
                    patch('connected_worker.run_one',side_effect=run):
                summary=await execute(None,tmp,prepared,path)
            credential.assert_called_once_with(enabled=True)
            self.assertNotIn('answer',summary)
            self.assertEqual((path/'inbox.sqlite').stat().st_mode & 0o777,0o600)
            with self.assertRaises(FileExistsError): await execute(None,tmp,prepared,path)
