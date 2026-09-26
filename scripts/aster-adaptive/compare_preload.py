"""Frozen preload comparison: actual PydanticAI versus Aster source slice.

No live model requests. Run each mode in a separate process; only summaries leave
memory. Both modes share Aster's exact fixture preload/payload construction.
"""
import argparse
import asyncio
import json
import math
import resource
import socket
import statistics
import sys
import time
from pathlib import Path
from unittest.mock import patch

from fixtures import CASES, content_digest, make_run
from offline_baseline import FixtureAdapter, FixtureRequest, digest


async def compare(mode):
    imported_at = time.perf_counter()
    if mode == 'pydanticai':
        from pydantic_ai import Agent, models
        from pydantic_ai.messages import ModelResponse, TextPart
        from pydantic_ai.models.function import FunctionModel
        from pydantic_ai.usage import UsageLimits
        models.ALLOW_MODEL_REQUESTS = False
    import_ms = (time.perf_counter() - imported_at) * 1000
    fixture = FixtureAdapter()
    records = []
    for case_id, prompt, ids in CASES:
        contract = make_run(fixture.source_digest, ids)
        allowed = {c.implementation for c in contract.projection.capabilities}
        tool_calls = 0
        async def execute(name, args):
            nonlocal tool_calls
            if name not in allowed or tool_calls >= contract.budget.tool_calls:
                raise AssertionError('denied fixture call')
            tool_calls += 1
            return {'fixture': True, 'status': 'available'}
        fixture.namespace['execute_tool'] = execute
        times = []
        response_steps = 0
        for i in range(210):
            tool_calls = 0
            response_steps = 0
            start = time.perf_counter()
            payload = await fixture.namespace['build_payload'](
                FixtureRequest(prompt), {'identity': 'Offline synthetic fixture'}, allowed)
            system_text = payload['messages'][0]['content']
            async def response(messages=None, info=None):
                nonlocal response_steps
                response_steps += 1
                if info is not None:
                    if info.function_tools:
                        raise AssertionError('preload profile must not advertise tools')
                    if info.instructions != system_text:
                        raise AssertionError('system instruction differs')
                    from pydantic_ai.messages import UserPromptPart
                    user_parts = [part.content for message in messages for part in message.parts
                                  if isinstance(part, UserPromptPart)]
                    if user_parts != [prompt]:
                        raise AssertionError('user context differs')
                    return ModelResponse(parts=[TextPart('Synthetic answer')])
                return 'Synthetic answer'
            if mode == 'pydanticai':
                agent = Agent(FunctionModel(response), instructions=system_text,
                              output_type=str, retries=0, capabilities=[])
                result = await asyncio.wait_for(agent.run(prompt, usage_limits=UsageLimits(request_limit=1)), timeout=10)
                text = result.output
            else:
                text = await response()
            if text != 'Synthetic answer' or tool_calls != len(ids) or response_steps != 1:
                raise AssertionError('fixture outcome mismatch')
            elapsed = (time.perf_counter()-start)*1000
            if i >= 10:
                times.append(elapsed)
        ordered = sorted(times)
        records.append({'case_id': case_id, 'samples': len(times), 'p50_ms': statistics.median(times),
                        'p95_ms': ordered[math.ceil(.95*len(times))-1], 'fixture_tool_calls': tool_calls,
                        'scripted_response_steps': response_steps, 'actual_model_requests': 0,
                        'prompt_tokens': None, 'context_text_bytes': len((system_text+prompt).encode())})
    return {'schema_version': 'preload-comparison.v1', 'mode': mode, 'cases': records,
            'candidate_import_ms': import_ms,
            'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform=='darwin' else 1024),
            'aster_source_digest': fixture.source_digest, 'dataset_digest': content_digest(CASES),
            'evaluator_digest': digest(Path(__file__).read_bytes()),
            'limits': ['fixed responses, no quality evidence', 'preload profile only',
                       'no provider request serialization or real token counts',
                       'fresh Agent per turn included; no tuning applied',
                       'separate processes; cross-mode runs are not temporally interleaved']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['aster', 'pydanticai'], required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        result = asyncio.run(compare(args.mode))
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'mode':args.mode, 'cases':len(result['cases']), 'model_requests':0}))


if __name__ == '__main__':
    main()
