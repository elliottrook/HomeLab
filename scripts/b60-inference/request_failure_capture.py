"""Undeployed bounded capture core for the fixed compatibility requests.

Transport and monotonic clock must be injected. No endpoint, key reader, CLI,
installation, lease or network default exists. Returned text/hidden reasoning
never leaves this function; only bounded metadata and a final-answer hash do.
"""
import hashlib
import json
import math
from pathlib import Path
import types

LEGACY=Path(__file__).parent/'model-trial-20261106-r2/guest_requests.py'
LEGACY_SHA='dbc596c5b77a8ea9359868798d621ff951c331754b2b4968c177b80d079e3dca'
MAXIMUM=1024*1024
FINISH={'stop','length','content_filter','tool_calls'}


def fixed_source(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEGACY_SHA:
        raise ValueError('fixed request source drift')
    module=types.ModuleType('verified_fixed_request_payload')
    # Verified bytes are interpreted once; neither legacy run() nor _key() is
    # invoked. The legacy module's main guard is false under this module name.
    exec(compile(raw,str(LEGACY),'exec'),module.__dict__)
    return module


def number(value):
    return type(value) in (int,float) and math.isfinite(value)


def tokens(value):
    return value if type(value) is int and value>=0 else None


def parse(status,raw,row):
    if type(status) is not int or not 100<=status<=599:
        row['outcome']='invalid_http_status';return
    row['http_status']=status
    if not isinstance(raw,bytes):
        row['outcome']='invalid_response_type';return
    row['response_bytes']=len(raw)
    if len(raw)>MAXIMUM:
        row['outcome']='response_too_large';return
    if status!=200:
        row['outcome']='http_error';return
    try:
        value=json.loads(raw);choice=value['choices'][0];message=choice['message']
        content=message.get('content');reasoning=message.get('reasoning_content')
        finish=choice.get('finish_reason')
        row['finish_reason']=finish if isinstance(finish,str) and finish in FINISH else 'unknown'
        row['final_chars']=len(content) if isinstance(content,str) else None
        row['reasoning_chars']=len(reasoning) if isinstance(reasoning,str) else None
        usage=value.get('usage');usage=usage if isinstance(usage,dict) else {}
        detail=usage.get('completion_tokens_details');detail=detail if isinstance(detail,dict) else {}
        row.update(prompt_tokens=tokens(usage.get('prompt_tokens')),
                   completion_tokens=tokens(usage.get('completion_tokens')),
                   reasoning_tokens=tokens(detail.get('reasoning_tokens')))
        if finish=='length':row['outcome']='token_limit';return
        if finish!='stop':row['outcome']='unsupported_finish';return
        if not isinstance(content,str) or not content.strip():
            row['outcome']='empty_final';return
        row['outcome']='returned_unscored'
        row['answer_sha256']=hashlib.sha256(content.encode()).hexdigest()
        if row['request']==1:row['arithmetic_exact']=content.strip().rstrip('.')=='42'
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,UnicodeError):
        row['outcome']='malformed_response'


def capture(transport,clock,*,source_path=LEGACY):
    """Preserve every attempt, including late/invalid/truncated responses.

    transport(payload_bytes, timeout_seconds=60, maximum_bytes=MAXIMUM+1)
    returns (integer_status, bounded_bytes). A future live adapter must prove
    that bound itself; this source-only core cannot confer execution authority.
    """
    source=fixed_source(source_path);rows=[]
    for index,prompt in enumerate(source.PROMPTS,1):
        row={'request':index,'outcome':'pending','transport_called':False,
             'elapsed_ms':None,'http_status':None,'finish_reason':None,
             'response_bytes':None,'final_chars':None,'reasoning_chars':None,
             'prompt_tokens':None,'completion_tokens':None,'reasoning_tokens':None,
             'answer_sha256':None,'arithmetic_exact':None}
        started=clock()
        if not number(started):
            row['outcome']='invalid_clock';rows.append(row);break
        row['transport_called']=True
        try:
            status,raw=transport(source.payload(prompt),timeout_seconds=source.TIMEOUT,
                                 maximum_bytes=MAXIMUM+1)
            parse(status,raw,row)
        except TimeoutError:row['outcome']='timeout'
        except Exception:row['outcome']='transport_error'
        finished=clock() # Includes response parsing/completeness checks.
        if not number(finished) or finished<started:
            row['outcome']='invalid_clock';row['answer_sha256']=None
        else:
            row['elapsed_ms']=round((finished-started)*1000)
            if finished-started>source.TIMEOUT:
                row['outcome']='deadline_exceeded';row['answer_sha256']=None
        rows.append(row)
        if row['outcome']!='returned_unscored':break
    complete=len(rows)==2 and all(r['outcome']=='returned_unscored' for r in rows)
    return {'schema':'b60-fixed-request-capture-prototype.v1',
            'state':'complete_unscored' if complete else 'failed',
            'planned_requests':2,'attempted_requests':sum(r['transport_called'] for r in rows),
            'records':rows,'retries':0,'fixed_request_source_sha256':LEGACY_SHA,
            'answer_content_retained':False,'hidden_reasoning_retained':False,
            'semantic_review_performed':False,'model_qualified':False,
            'ready_for_live_execution':False}
