"""Explicit-execution local development runner; defaults to a dry-run plan.

Run only within a separately approved shared-service window. Authentication is
provided by the existing host environment, never a CLI argument or output field.
"""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.request
from sa3_investigation import investigate

BASE = 'http://192.168.70.12:11435'


def sanitize_response(value, elapsed):
    choice = value['choices'][0]
    message = choice['message']
    try:
        answer = json.loads(message.get('content') or '')
    except (ValueError, TypeError):
        answer = None
    # Thought text is discarded here; only aggregate metadata leaves transport.
    reasoning = message.get('reasoning_content') or ''
    return {'answer': answer, 'finish_reason': choice.get('finish_reason'),
            'latency_seconds': round(elapsed, 3), 'reasoning_present': bool(reasoning),
            'reasoning_characters': len(reasoning),
            'completion_tokens': value.get('usage', {}).get('completion_tokens'),
            'tool_call_count': len(message.get('tool_calls') or [])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    cases = json.loads(Path(__file__).with_name('sa3-investigation-development.json').read_text())['cases']
    schedule = [(cases[0], 'nonthinking'), (cases[0], 'thinking'),
                (cases[1], 'thinking'), (cases[1], 'nonthinking')]
    if not args.execute:
        print(json.dumps({'execute': False, 'cases': [c['id'] for c in cases],
                          'sessions': 4, 'max_model_calls': 12,
                          'session_seconds': 300, 'request_seconds': 240,
                          'scope': 'synthetic development only; no model-quality gate'}))
        return 0
    key = os.environ.get('ASTER_LLAMA_API_KEY')
    if not key:
        raise SystemExit('Existing service authentication required; no request made')
    headers = {'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'}

    def get(path):
        with urllib.request.urlopen(urllib.request.Request(BASE+path, headers=headers), timeout=10) as response:
            return response.read().decode()

    def idle_healthy():
        health = json.loads(get('/health'))
        processing = [float(line.split()[-1]) for line in get('/metrics').splitlines()
                      if line and not line.startswith('#')
                      and line.split()[0].split('{')[0].endswith('requests_processing')]
        return health.get('status') == 'ok' and bool(processing) and not any(processing)

    def transport(payload, timeout):
        start = time.monotonic()
        request = urllib.request.Request(BASE+'/v1/chat/completions', headers=headers,
                                         data=json.dumps(payload).encode())
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.load(response)
        return sanitize_response(value, time.monotonic()-start)

    for case, mode in schedule:
        if not idle_healthy():
            print(json.dumps({'stopped': 'service_not_confirmed_idle_healthy'}), flush=True)
            return 1
        result = investigate(case, mode, 'qwen3.8-27b', transport)
        print(json.dumps(result, sort_keys=True), flush=True)
        if result['status'].startswith('transport_error') or result['status'] == 'time_budget_exhausted':
            print(json.dumps({'stopped': 'budget_or_transport_failure_no_retry'}), flush=True)
            return 1
    print(json.dumps({'postcheck_idle_healthy': idle_healthy()}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
