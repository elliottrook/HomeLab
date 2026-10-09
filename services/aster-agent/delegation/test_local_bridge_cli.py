"""No-inference CLI contract tests; no Codex process is started."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from local_bridge_cli import main, recorded_status, recover_snapshot, reviewed_request
from store import DispatchStore


class LocalBridgeCLITests(unittest.TestCase):
    def test_default_is_inert(self):
        output=io.StringIO()
        with redirect_stdout(output): main([])
        self.assertEqual(json.loads(output.getvalue()),
                         {'enabled':False,'inference':False})

    def test_exact_reviewed_frame_has_no_extra_authority(self):
        frame=dict(request_id='12345678-1234-1234-1234-123456789abc',
                   text='synthetic public question',cloud_consent=True,local_only=False)
        job,text=reviewed_request(json.dumps(frame).encode())
        self.assertEqual(job,'request-'+frame['request_id'])
        self.assertEqual(text,frame['text'])
        for change in ({'local_only':True},{'cloud_consent':False},
                       {'tools':['shell']},{'owner':'other'},{'model':'other'}):
            bad=dict(frame,**change)
            with self.assertRaises(ValueError):
                reviewed_request(json.dumps(bad).encode())

    def test_invalid_or_oversized_frame_fails_before_startup(self):
        for raw in (b'',b'[]',b'not json',b'x'*20001,
                    json.dumps(dict(request_id='invalid',text='text',
                                    cloud_consent=True,local_only=False)).encode()):
            with self.assertRaises((ValueError,TypeError)):
                reviewed_request(raw)

    def test_status_is_owner_bound_and_read_only_without_codex(self):
        identifier='request-12345678-1234-1234-1234-123456789abc'
        with tempfile.TemporaryDirectory() as root:
            state=Path(root).resolve()/'state'
            state.mkdir(mode=0o700)
            db=state/'jobs.sqlite'
            store=DispatchStore(db)
            self.assertTrue(store.claim(identifier,'thread-1','uid:'+str(os.getuid())))
            store.bind(identifier,'thread-1','turn-1')
            store.finish(identifier,'thread-1','turn-1','completed')
            foreign='request-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
            self.assertTrue(store.claim(foreign,'thread-2','uid:other'))
            store.close()
            os.chmod(db,0o600)
            output=io.StringIO()
            with redirect_stdout(output):
                main(['--status','--state-dir',str(state),'--request-id',identifier])
            self.assertEqual(json.loads(output.getvalue()),
                             {'id':identifier,'recorded':True,
                              'state':'completed','turn_recorded':True})
            self.assertEqual(recorded_status(state,
                foreign)['state'],'unrecorded')
            self.assertEqual(len(list(state.iterdir())),1)
            with self.assertRaises(ValueError):
                recorded_status(state,'../invalid')
            link=Path(root)/'link'
            link.symlink_to(state)
            with self.assertRaises(ValueError):
                recorded_status(link,identifier)

    def test_recovery_accepts_only_exact_completed_full_turn_without_tools(self):
        snapshot={'thread':{'id':'thread-1','turns':[{'id':'turn-1',
            'status':'completed','itemsView':'full','items':[
                {'type':'userMessage','text':'Fictional question'},
                {'type':'agentMessage','phase':'final_answer','text':'Final answer'}]}]}}
        self.assertEqual(recover_snapshot(snapshot,'thread-1','turn-1'),'Final answer')
        for altered in (
            {'thread':{'id':'other','turns':snapshot['thread']['turns']}},
            {'thread':{'id':'thread-1','turns':[]}},
            {'thread':{'id':'thread-1','turns':[dict(snapshot['thread']['turns'][0],itemsView='partial')]}},
            {'thread':{'id':'thread-1','turns':[dict(snapshot['thread']['turns'][0],
                items=snapshot['thread']['turns'][0]['items']+[{'type':'commandExecution'}])]}},
        ):
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                recover_snapshot(altered,'thread-1','turn-1')

    def test_recovery_cli_reads_bound_turn_without_starting_inference(self):
        identifier='request-12345678-1234-1234-1234-123456789abc'
        calls=[]
        class FakeClient:
            def __init__(self,*args,**kwargs):pass
            def call(self,method,params):
                calls.append(method)
                if method=='config/read':return {'config':{'mcp_servers':{}}}
                if method=='thread/read':
                    self_ref=params['threadId']
                    return {'thread':{'id':self_ref,'turns':[{'id':'turn-1',
                        'status':'completed','itemsView':'full','items':[
                            {'type':'agentMessage','phase':'final_answer','text':'Recovered'}]}]}}
                raise AssertionError(method)
            def close(self):pass
        output=io.StringIO()
        with patch('local_bridge_cli.recorded_row',return_value=('completed','thread-1','turn-1')), \
             patch('local_bridge_cli.shutil.which',return_value='/fake/codex'), \
             patch('local_bridge_cli.RecoveryConfigClient',FakeClient), \
             patch('local_bridge_cli.initialize'), \
             patch('local_bridge_cli.options',return_value=[]), \
             patch('local_bridge_cli.prepared_manifest',return_value={'model':'fake'}), \
             patch('local_bridge_cli.fingerprint',return_value='a'*64), \
             redirect_stdout(output):
            main(['--recover','--approved-sha256','a'*64,'--state-dir','/private/tmp',
                  '--request-id',identifier])
        result=json.loads(output.getvalue())
        self.assertEqual(result['answer'],'Recovered')
        self.assertFalse(result['inference'])
        self.assertEqual(calls,['config/read','thread/read'])
