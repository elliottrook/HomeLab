"""Actual Aster chat-loop source versus minimal PydanticAI, fixture-only."""
from __future__ import annotations

import argparse
import ast
import asyncio
import json
import math
import socket
import statistics
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Literal
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, ValidationError
from offline_baseline import SOURCE, digest

MANIFEST = Path(__file__).parent/'fixtures/tool-loop-v1.json'


class TimeArguments(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    timezone: Literal['UTC']


class EmptyArguments(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class FixtureHTTPError(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)


class Boundary:
    def __init__(self):
        self.enabled = True
        self.now = 1000
        self.expires_at = 1200
        self.attempts = 0
        self.executed = []
        self.denials = 0

    async def execute(self, name, args):
        self.attempts += 1
        if (not self.enabled or self.now >= self.expires_at or self.attempts > 8
                or name not in {'get_current_time', 'get_forgejo_report'}):
            self.denials += 1
            return {'error':'fixture policy denied'}
        try:
            (TimeArguments if name == 'get_current_time' else EmptyArguments).model_validate(args)
        except ValidationError:
            self.denials += 1
            return {'error':'fixture arguments denied'}
        self.executed.append(name)
        return {'fixture':True,'status':'available'}


def aster_chat():
    node = next(n for n in ast.parse(SOURCE.read_bytes()).body
                if isinstance(n, ast.AsyncFunctionDef) and n.name == 'chat')
    node.decorator_list = []
    tree = ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),node],type_ignores=[])
    ast.fix_missing_locations(tree)
    namespace = {'json':json,'uuid':uuid,'HTTPException':FixtureHTTPError,'MAX_TOOL_ROUNDS':3,'UPSTREAM_MODEL':'fixture'}
    exec(compile(tree,str(SOURCE),'exec'),namespace)
    return namespace


async def run_case(mode, case):
    boundary, steps, proposed = Boundary(), 0, 0
    def next_response():
        nonlocal steps, proposed
        if steps >= 4:
            raise FixtureHTTPError(502,'script exhausted')
        response = case['responses'][min(steps,len(case['responses'])-1)]
        steps += 1
        if response.get('revoke'):
            boundary.enabled = False
        if response.get('expire'):
            boundary.now = boundary.expires_at
        if 'tool' in response:
            proposed += 1
        return response
    if mode == 'aster':
        namespace = aster_chat()
        namespace['PERSONAS'] = {'fixture':{'tools':{'get_current_time','get_forgejo_report'}}}
        async def noop(*_):
            return None
        namespace['lab_operations'] = SimpleNamespace(chat=lambda *_:None,plan=noop)
        async def payload(*_):
            return {'messages':[{'role':'user','content':'Synthetic loop fixture'}]}
        namespace['build_payload'] = payload
        namespace['execute_tool'] = boundary.execute
        async def response(*_):
            r = next_response()
            message = {'role':'assistant','content':r.get('text','')}
            if 'tool' in r:
                message['tool_calls'] = [{'id':f'c{steps}','type':'function','function':{
                    'name':r['tool'],'arguments':r['arguments'] if isinstance(r['arguments'],str) else json.dumps(r['arguments'])}}]
            return {'choices':[{'message':message}],'usage':{}}
        namespace['upstream_completion'] = response
        request = SimpleNamespace(persona='fixture',enabled_tools=None,stream=False,progress=False)
        execute = lambda: namespace['chat'](request)
    else:
        from pydantic_ai import Agent, models
        from pydantic_ai.models.function import FunctionModel
        from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
        from pydantic_ai.usage import UsageLimits
        models.ALLOW_MODEL_REQUESTS = False
        async def get_current_time(timezone: Literal['UTC']):
            return await boundary.execute('get_current_time',{'timezone':timezone})
        async def get_forgejo_report():
            return await boundary.execute('get_forgejo_report',{})
        async def response(*_):
            r = next_response()
            return ModelResponse(parts=[ToolCallPart(r['tool'],r['arguments'])] if 'tool' in r
                                 else [TextPart(r['text'])])
        agent = Agent(FunctionModel(response),tools=[get_current_time,get_forgejo_report],
                      retries=3,capabilities=[])
        execute = lambda: agent.run('Synthetic loop fixture',usage_limits=UsageLimits(request_limit=4,tool_calls_limit=8))
    started = time.perf_counter()
    status, error_type = 'completed', None
    try:
        await asyncio.wait_for(execute(),10)
    except Exception as error:
        status, error_type = 'failed', type(error).__name__
    return {'status':status,'error_type':error_type,'executed':boundary.executed,
            'boundary_attempts':boundary.attempts,'boundary_denials':boundary.denials,
            'proposed':proposed,'response_steps':steps,'actual_model_requests':0,
            'elapsed_ms':(time.perf_counter()-started)*1000}


async def measure(mode):
    dataset = json.loads(MANIFEST.read_text())
    rows = []
    for case in dataset['cases']:
        result = await run_case(mode,case)
        passed = result['status']==case['expected_status'] and result['executed']==case['expected_calls']
        row={'case_id':case['id'],'conformance_passed':passed,'observed':result}
        if not passed:
            rows.append(row)
            continue
        if case['id'] in {'one-read','two-sequential-reads'}:
            samples=[]
            for i in range(210):
                r=await run_case(mode,case)
                if r['status']!=case['expected_status'] or r['executed']!=case['expected_calls']:
                    raise AssertionError('repeated conformance failed')
                if i>=10:
                    samples.append(r['elapsed_ms'])
            row['timing']={'samples':200,'p50_ms':statistics.median(samples),
                           'p95_ms':sorted(samples)[math.ceil(.95*len(samples))-1]}
        rows.append(row)
    return {'schema_version':'tool-loop-comparison.v1','mode':mode,'cases':rows,
            'dataset_digest':digest(MANIFEST.read_bytes()),'evaluator_digest':digest(Path(__file__).read_bytes()),
            'aster_source_digest':digest(SOURCE.read_bytes()),
            'limits':['synthetic responses, no quality evidence','setup excluded from timed loop for both candidates',
                      'baseline payload and Lab Operations are stubs','policy enforced by shared independent fixture boundary']}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['aster','pydanticai'],required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        result=asyncio.run(measure(args.mode))
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    failures=[x['case_id'] for x in result['cases'] if not x['conformance_passed']]
    print(json.dumps({'mode':args.mode,'cases':len(result['cases']),'failures':failures}))
    if failures:
        raise SystemExit(1)


if __name__=='__main__':
    main()
