"""One fixed three-answer accepted9B post-reset qualification; inert by default.

This is not the27B milestone, a matched latency baseline, or a retry of News.
No raw answer/reasoning, credentials, error body or exception text is emitted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import time
import urllib.error
import urllib.request

MODEL='/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf'
ENDPOINT='http://192.168.70.12:11435/v1/chat/completions'
KEY_FILE=Path('/etc/aster-llama-api-keys')
MAXIMUM=1024*1024
PROMPTS=(
    'Fictional hardware self-test. Return only the number: what is 17 plus 25?',
    'Fictional facts: backup_state is failed. Return only the JSON object with keys backup_ok and next_action; backup_ok must be false and next_action must be inspect. Do not claim to perform any action.',
    'Fictional facts: a motion sensor has no battery and its report has no timestamp. Return only the JSON object with keys current_state_known and safe_next_check; current_state_known must be false and safe_next_check must be inspect_timestamp. Do not claim to perform any action.',
)
EXPECTED=(
    '42',
    {'backup_ok':False,'next_action':'inspect'},
    {'current_state_known':False,'safe_next_check':'inspect_timestamp'},
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def key_reader():
    values=[v.strip() for v in KEY_FILE.read_text().splitlines() if v.strip()]
    if not 1<=len(values)<=16 or any(len(v)<16 for v in values):raise ValueError('KEY_CUSTODY_FORM')
    return values[0]


def payload(index):
    if type(index) is not int or not 0<=index<3:raise ValueError('FIXED_REQUEST_ID')
    return json.dumps({'model':MODEL,'messages':[{'role':'user','content':PROMPTS[index]}],
        'temperature':0,'max_tokens':128,'stream':False,'chat_template_kwargs':{'enable_thinking':False}},sort_keys=True,separators=(',',':')).encode()


def verify_response(index,status,raw):
    out={'http_status':status if type(status) is int and 100<=status<=599 else None,
         'finish_reason':None,'answer_sha256':None,'predicate_passed':False,'outcome':'invalid_response'}
    if status!=200 or type(status) is not int:
        out['outcome']='http_error';return out
    if not isinstance(raw,bytes) or len(raw)>MAXIMUM:return out
    try:
        value=json.loads(raw)
        if value.get('model')!=MODEL:return out
        choices=value.get('choices')
        if type(choices) is not list or len(choices)!=1:return out
        choice=choices[0];finish=choice.get('finish_reason')
        out['finish_reason']=finish if finish in ('stop','length','content_filter','tool_calls') else 'unknown'
        if finish!='stop':out['outcome']='incomplete_answer';return out
        message=choice.get('message');content=message.get('content')
        if type(content) is not str or not content.strip():return out
        if message.get('reasoning_content'):
            out['outcome']='reasoning_mode_mismatch';return out
        expected=EXPECTED[index]
        actual=content.strip() if index==0 else json.loads(content)
        # Canonical JSON preserves bool versus integer distinctions.
        passed=(actual==expected if index==0 else
            json.dumps(actual,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':')))
        out['predicate_passed']=passed
        out['answer_sha256']=hashlib.sha256(content.encode()).hexdigest()
        out['outcome']='passed' if passed else 'wrong_answer'
    except (ValueError,TypeError,AttributeError,KeyError,IndexError,UnicodeError):pass
    return out


def alarm(signum,frame):raise TimeoutError()


def run(*,read_key=key_reader,opener=None,clock=time.monotonic):
    key=read_key();opener=opener or urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    rows=[]
    for index in range(3):
        req=urllib.request.Request(ENDPOINT,data=payload(index),method='POST',
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        started=clock();previous=signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,30)
        try:
            try:
                with opener.open(req,timeout=30) as response:status,raw=response.status,response.read(MAXIMUM+1)
                row=verify_response(index,status,raw)
            except urllib.error.HTTPError as error:
                row=verify_response(index,error.code,b'')
            except Exception:
                row={'http_status':None,'finish_reason':None,'answer_sha256':None,'predicate_passed':False,'outcome':'transport_failure'}
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
        elapsed=clock()-started
        row.update(request=index+1,elapsed_ms=round(elapsed*1000))
        if elapsed<0 or elapsed>30:row.update(predicate_passed=False,outcome='deadline_exceeded',answer_sha256=None)
        rows.append(row)
        if row['predicate_passed'] is not True:break
    return {'schema':'b60-post-xe-known-answer-packet.v1','state':'passed' if len(rows)==3 and all(r['predicate_passed'] for r in rows) else 'failed',
        'planned_requests':3,'attempted_requests':len(rows),'max_tokens':128,'timeout_seconds':30,
        'retries':0,'records':rows,'answer_content_retained':False,'hidden_reasoning_retained':False,
        'device_recovery_qualified':False,'requires_independent_source_bound_restoration_acceptance':True}


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-authorized',action='store_true');args=p.parse_args()
    if not args.run_authorized:print(json.dumps({'state':'disabled','requests':0}));return 0
    print(json.dumps(run(),sort_keys=True,separators=(',',':')),flush=True)
    return 0 # The qualified host persists metadata before accepting/rejecting.


if __name__=='__main__':raise SystemExit(main())
