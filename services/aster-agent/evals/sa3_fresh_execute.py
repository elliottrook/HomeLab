"""Explicit-execution wrapper for a frozen label-free local evaluation package."""
import argparse
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from sa3_fresh_package import run_package, validate_cases
from sa3_investigation_runner import sanitize_response

BASE = 'http://192.168.70.12:11435'
MAX_HTTP_BYTES = 1_048_576
MAX_INPUT_BYTES = 1_048_576


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON key in evaluation input')
        value[key] = item
    return value


def _reject_non_json_constant(value):
    raise ValueError(f'non-JSON numeric constant in evaluation data: {value}')


def decode_unique_json(raw):
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_constant=_reject_non_json_constant)


def load_bounded_json(path, limit=MAX_INPUT_BYTES):
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('evaluation input exceeds bounded envelope')
    return decode_unique_json(raw)


def read_bounded(response, limit=MAX_HTTP_BYTES):
    raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('local service response exceeds bounded envelope')
    return raw.decode('utf-8')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect forbidden', headers, fp)


def build_local_opener():
    # Do not send the fixed local-service bearer credential through a proxy
    # inherited from the invoking environment.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def parse_processing_metric(raw):
    """Return the sole finite, nonnegative requests-processing gauge."""
    values = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        name = fields[0].split('{', 1)[0]
        if not name.endswith('requests_processing'):
            continue
        try:
            value = float(fields[-1])
        except ValueError as exc:
            raise ValueError('invalid requests-processing metric') from exc
        if not math.isfinite(value) or value < 0:
            raise ValueError('invalid requests-processing metric')
        values.append(value)
    if len(values) != 1:
        raise ValueError('exactly one requests-processing metric required')
    return values[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--expected-release-digest', required=True)
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    bundle = load_bounded_json(args.cases)
    manifest = load_bounded_json(args.manifest)
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
    opener = build_local_opener()

    def get(path):
        request = urllib.request.Request(BASE+path, headers=headers)
        with opener.open(request, timeout=10) as response:
            return read_bounded(response)

    def ready():
        health = decode_unique_json(get('/health'))
        processing = parse_processing_metric(get('/metrics'))
        return health.get('status') == 'ok' and processing == 0

    def transport(payload, timeout):
        start = time.monotonic()
        request = urllib.request.Request(BASE+'/v1/chat/completions', headers=headers,
                                         data=json.dumps(payload).encode())
        with opener.open(request, timeout=timeout) as response:
            value = decode_unique_json(read_bounded(response))
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
