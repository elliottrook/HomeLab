import tempfile
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch
from connected_worker import execute,connected_manifest
from handoff import Gateway
from request_intake import RequestBody,RequestIntake
from test_worker import Agent


class ReviewedWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_reviewed_text_completes_once_without_manifest_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();g=Gateway(root/'gateway','aster-gateway')
            self.addCleanup(g.close)
            intake=RequestIntake(g,'fixture',enabled=True)
            text='Fictional user-reviewed question with no imported history.'
            body=RequestBody(request_id=uuid.uuid4(),text=text,cloud_consent=True,local_only=False)
            receipt=intake.submit('owner',body);jid=receipt['id']
            prepared=connected_manifest({'model':'fixture','reasoning_effort':'medium','fixture':'old'},jid,receipt['request_sha256'])
            self.assertNotIn('fixture',prepared['base']);self.assertNotIn(text,str(prepared))
            class Client:
                def __init__(self,*args,**kwargs):pass
                async def offer(self,j):return g.offer('aster-codex-worker-mac',j)
                async def payload(self,j,d):return intake.assigned_payload('aster-codex-worker-mac',j,d)
                async def receipt(self,j,v):return g.receipt('aster-codex-worker-mac',j,**v)
                async def controls(self,j,d):return g.controls('aster-codex-worker-mac',j,d)
                async def answer(self,j,d,a):return g.deliver_answer('aster-codex-worker-mac',j,d,a)
                async def usage(self,j,d,u):return g.report_usage('aster-codex-worker-mac',j,d,u)
            seen=[]
            class FakeAgent(Agent):
                def __init__(self,*args):super().__init__()
                def start(self,request):seen.append(str(request));return super().start(request)
                def close(self):pass
            with patch('connected_worker.WorkerSession'),patch('connected_worker.connection_check'), \
                    patch('connected_worker.WorkerClient',Client),patch('connected_worker.PipeAgent',FakeAgent):
                result=await execute(None,tmp,prepared,root/'run')
                self.assertEqual(result['state'],'completed')
                again=await execute(None,tmp,prepared,root/'run2')
                self.assertEqual(again['state'],'unconfirmed')
            self.assertEqual(len(seen),1);self.assertIn(text,seen[0])
            self.assertEqual(g.owner_result('owner',jid)['answer'],'Verified result')
            for p in (root/'run').rglob('*'):
                if p.is_file():self.assertNotIn(text.encode(),p.read_bytes())
