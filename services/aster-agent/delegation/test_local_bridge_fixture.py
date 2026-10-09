"""Full synthetic stdio round trip; fake Codex executable, no network/model."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('local_bridge_cli.py')
FAKE = '''#!/usr/bin/env python3
import json,os,sys
features={name:False for name in (
    "shell_tool","unified_exec","apps","plugins","hooks","browser_use",
    "computer_use","multi_agent","code_mode","code_mode_host","memories",
    "image_generation","view_image","skill_search","shell_snapshot")}
config={"features":features,"mcp_servers":{},"web_search":"disabled",
        "sandbox_mode":"read-only","model_provider":"openai",
        "model":"gpt-5.6-luna","model_reasoning_effort":"medium"}
for raw in sys.stdin:
    request=json.loads(raw)
    if "id" not in request:continue
    method=request.get("method")
    result={"initialize":{},"config/read":{"config":config},
            "account/read":{"account":{"type":"chatgpt"}},
            "model/list":{"data":[{"model":"gpt-5.6-luna"}]},
            "thread/start":{"thread":{"id":"t"}},
            "turn/start":{"turn":{"id":"u"}}}.get(method)
    print(json.dumps({"id":request["id"],"result":result}),flush=True)
    if method=="turn/start":
        with open(os.environ["FAKE_TURN_LOG"],"a") as log:log.write("turn\\n")
        print(json.dumps({"method":"item/completed","params":{"threadId":"t",
              "turnId":"u","item":{"id":"a","type":"agentMessage",
              "phase":"final_answer","text":"Synthetic answer"}}}),flush=True)
        print(json.dumps({"method":"turn/completed","params":{"threadId":"t",
              "turn":{"id":"u","status":"completed"}}}),flush=True)
'''


class LocalBridgeFixtureTests(unittest.TestCase):
    def test_one_synthetic_turn_and_duplicate_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            executable=root/'codex'
            executable.write_text(FAKE)
            executable.chmod(0o700)
            log=root/'turns.txt'
            env=dict(os.environ,PATH=str(root)+':/usr/bin:/bin',FAKE_TURN_LOG=str(log))
            prepared=subprocess.run([sys.executable,str(SCRIPT),'--prepare'],
                env=env,capture_output=True,text=True,timeout=15,check=True)
            value=json.loads(prepared.stdout)
            self.assertFalse(value['inference'])
            self.assertEqual(value['manifest']['auth'],'chatgpt')
            self.assertEqual(value['manifest']['enabled_mcp_count'],0)
            frame=dict(request_id='12345678-1234-1234-1234-123456789abc',
                       text='Fictional question without a real model',
                       cloud_consent=True,local_only=False)
            state=(root/'state').resolve()
            cmd=[sys.executable,str(SCRIPT),'--run','--approved-sha256',
                 value['manifest_sha256'],'--state-dir',str(state)]
            first=subprocess.run(cmd,input=json.dumps(frame),env=env,
                capture_output=True,text=True,timeout=15)
            self.assertEqual(first.returncode,0,first.stderr)
            result=json.loads(first.stdout)
            self.assertEqual(result['state'],'completed')
            self.assertEqual(result['answer'],'Synthetic answer')
            self.assertFalse(result['automatic_retry'])
            self.assertGreaterEqual(result['elapsed_seconds'],0)
            self.assertEqual(log.read_text(),'turn\n')
            status=subprocess.run([sys.executable,str(SCRIPT),'--status',
                '--state-dir',str(state),'--request-id','request-'+frame['request_id']],
                env=env,capture_output=True,text=True,timeout=15,check=True)
            self.assertEqual(json.loads(status.stdout)['state'],'completed')
            self.assertEqual(log.read_text(),'turn\n')
            self.assertNotIn(frame['text'],(state/'jobs.sqlite').read_bytes().decode('latin1'))
            self.assertNotIn('Synthetic answer',(state/'jobs.sqlite').read_bytes().decode('latin1'))
            second=subprocess.run(cmd,input=json.dumps(frame),env=env,
                capture_output=True,text=True,timeout=15)
            self.assertNotEqual(second.returncode,0)
            self.assertEqual(log.read_text(),'turn\n')
