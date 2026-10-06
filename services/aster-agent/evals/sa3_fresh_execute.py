"""Explicit-execution wrapper for a frozen label-free local evaluation package."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from sa3_fresh_package import run_package, validate_cases
from sa3_investigation_runner import sanitize_response

BASE = 'http://192.168.70.12:11435'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect forbidden', headers, fp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--expected-release-digest', required=True)
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    bundle = json.loads(args.cases.read_text())
    manifest = json.loads(args.manifest.read_text())
    if manifest.get('release_digest') != args.expected_release_digest:
        raise SystemExit('Release does not match explicitly selected digest')
    validate_cases(bundle, manifest)
    if not args.execute:
        print(json.dumps({'status': 'dry_run_valid', 'release': args.expected_release_digest,
                          'cases': 20, 'sessions': 40, 'max_model_calls': 120,
                          'max_inference_minutes': 200, 'keys_accessed': False}))
        return 0
    if args.ledger is None:
        raise SystemExit('Explicit durable ledger path required')
    key = os.environ.get('ASTER_LLAMA_API_KEY')
    if not key:
        raise SystemExit('Existing local service authentication required')
    headers = {'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'}
    opener = urllib.request.build_opener(NoRedirect())

    def get(path):
        request = urllib.request.Request(BASE+path, headers=headers)
        with opener.open(request, timeout=10) as response:
            return response.read().decode()

    def ready():
        health = json.loads(get('/health'))
        processing = [float(line.split()[-1]) for line in get('/metrics').splitlines()
                      if line and not line.startswith('#')
                      and line.split()[0].split('{')[0].endswith('requests_processing')]
        return health.get('status') == 'ok' and bool(processing) and not any(processing)

    def transport(payload, timeout):
        start = time.monotonic()
        request = urllib.request.Request(BASE+'/v1/chat/completions', headers=headers,
                                         data=json.dumps(payload).encode())
        with opener.open(request, timeout=timeout) as response:
            value = json.load(response)
        result = sanitize_response(value, time.monotonic()-start)
        # A content-free progress event; model answers remain in the private ledger.
        print(json.dumps({'event': 'request_complete', 'seconds': result['latency_seconds'],
                          'finish_reason': result['finish_reason']}), flush=True)
        return result

    result = run_package(bundle, manifest, args.ledger, transport, ready)
    result['postcheck_idle_healthy'] = ready()
    print(json.dumps(result), flush=True)
    return 0 if result['status'] == 'complete' and result['postcheck_idle_healthy'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
