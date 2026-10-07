import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
try:
    import httpx
except ImportError:
    httpx = None


@unittest.skipIf(httpx is None,'Run with pinned gateway dependencies')
class AssembledPilotTests(unittest.IsolatedAsyncioTestCase):
    async def test_whole_offline_run_saves_owner_answer_and_private_state(self):
        from assembled_pilot import execute, assembled_manifest
        from test_worker import Agent
        class FakePipe(Agent):
            def __init__(self, *args): super().__init__()
            def close(self): pass
        prepared = assembled_manifest({'model':'model','reasoning_effort':'medium'})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'result'
            with patch('assembled_pilot.PipeAgent', FakePipe), contextlib.redirect_stdout(io.StringIO()) as text:
                await execute(None,directory,prepared,output)
            result = json.loads((output/'result.json').read_text())
            self.assertEqual(result['state'],'completed')
            self.assertEqual(result['owner_view']['reply'],'Verified result')
            self.assertFalse(result['production_deployment'])
            self.assertEqual(json.loads(text.getvalue())['usage_status'],'unknown')
            for path in (output, output/'result.json', output/'inbox.sqlite', output/'gateway.sqlite'):
                self.assertEqual(path.stat().st_mode & 0o077,0)
            with self.assertRaises(FileExistsError):
                await execute(None,directory,prepared,output)

    async def test_manifest_includes_execution_adapters(self):
        from assembled_pilot import assembled_manifest
        value = assembled_manifest({'model':'model'})
        for name in ('assembled_pilot.py','worker.py','pipe_worker.py','handoff.py','worker_client.py','session.py'):
            self.assertIn(name,value['source_hashes'])
        self.assertEqual(value['maximum_model_turns'],1)
        self.assertFalse(value['automatic_retry'])

    async def test_stop_after_ack_uses_owner_route_and_requires_terminal(self):
        from assembled_pilot import execute, assembled_manifest
        from test_worker import Agent
        from test_contract import end
        class FakePipe(Agent):
            def __init__(self, *args): super().__init__()
            def interrupt(self, request):
                super().interrupt(request)
                self.events = [end('interrupted')]
            def close(self): pass
        prepared = assembled_manifest({'model':'model','reasoning_effort':'medium'},cancel_after_ack=True)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'result'
            with patch('assembled_pilot.PipeAgent', FakePipe), contextlib.redirect_stdout(io.StringIO()):
                await execute(None,directory,prepared,output)
            result = json.loads((output/'result.json').read_text())
            self.assertTrue(result['cancellation_requested'])
            self.assertTrue(result['cancellation_confirmed'])
            self.assertEqual(result['state'],'interrupted')
            self.assertIsNone(result['owner_view']['reply'])
