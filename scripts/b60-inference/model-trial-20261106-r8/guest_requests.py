"""Fixed source-local transport; emit bounded metadata for request failures.

The explicit CLI switch is used only by the source/card-bound independent
runner. It is not booking authority. No redirects, proxies, retries, text,
exception strings, credentials or hidden reasoning enter the returned packet.
"""
import argparse
import json
import signal
import time
import urllib.error
import urllib.request
from pathlib import Path

from request_failure_capture import capture, MAXIMUM, LEGACY_SHA, fixed_source, LEGACY

ENDPOINT = 'http://192.168.70.12:11435/v1/chat/completions'
KEY_FILE = Path('/etc/aster-llama-api-keys')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def key_reader():
    # Exact existing source-local custody; no key bytes leave this process.
    return fixed_source(LEGACY)._key(KEY_FILE)


def alarm(signum, frame):
    raise TimeoutError()


def transport_for(key, opener):
    def transport(payload, *, timeout_seconds, maximum_bytes):
        if timeout_seconds != 60 or maximum_bytes != MAXIMUM + 1:
            raise ValueError('fixed transport bounds')
        req = urllib.request.Request(ENDPOINT, data=payload, method='POST',
              headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        previous = signal.signal(signal.SIGALRM, alarm)
        signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
        try:
            try:
                with opener.open(req, timeout=timeout_seconds) as response:
                    return response.status, response.read(maximum_bytes)
            except urllib.error.HTTPError as error:
                # Do not read an error body or follow a redirect with a key.
                return error.code, b''
            except urllib.error.URLError as error:
                if isinstance(error.reason, TimeoutError):
                    raise TimeoutError() from None
                raise OSError() from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
    return transport


def validate_packet(packet):
    # Reconstruct only explicit bounded fields; reject arbitrary guest output.
    required = {'schema', 'state', 'planned_requests', 'attempted_requests',
        'records', 'retries', 'fixed_request_source_sha256', 'answer_content_retained',
        'hidden_reasoning_retained', 'semantic_review_performed', 'model_qualified',
        'ready_for_live_execution'}
    assert type(packet) is dict and set(packet) == required
    assert packet['schema'] == 'b60-fixed-request-capture-prototype.v1'
    assert packet['state'] in {'failed', 'complete_unscored'}
    assert packet['fixed_request_source_sha256'] == LEGACY_SHA
    assert packet['planned_requests'] == 2 and packet['retries'] == 0
    assert type(packet['attempted_requests']) is int and 0 <= packet['attempted_requests'] <= 2
    assert all(packet[k] is False for k in ('answer_content_retained', 'hidden_reasoning_retained',
          'semantic_review_performed', 'model_qualified', 'ready_for_live_execution'))
    records = packet['records']
    assert type(records) is list and 1 <= len(records) <= 2
    fields = {'request', 'outcome', 'transport_called', 'elapsed_ms', 'http_status',
        'finish_reason', 'response_bytes', 'final_chars', 'reasoning_chars', 'prompt_tokens',
        'completion_tokens', 'reasoning_tokens', 'answer_sha256', 'arithmetic_exact'}
    outcomes = {'invalid_http_status', 'invalid_response_type', 'response_too_large',
        'http_error', 'token_limit', 'unsupported_finish', 'empty_final',
        'returned_unscored', 'malformed_response', 'invalid_clock', 'timeout',
        'transport_error', 'deadline_exceeded'}
    for i, row in enumerate(records, 1):
        assert type(row) is dict and set(row) == fields and row['request'] == i
        assert row['outcome'] in outcomes and type(row['transport_called']) is bool
        assert row['finish_reason'] in {None, 'stop', 'length', 'content_filter', 'tool_calls', 'unknown'}
        for k in ('elapsed_ms', 'response_bytes', 'final_chars', 'reasoning_chars',
                  'prompt_tokens', 'completion_tokens', 'reasoning_tokens'):
            assert row[k] is None or type(row[k]) is int and 0 <= row[k] <= 2**53
        assert row['http_status'] is None or type(row['http_status']) is int and 100 <= row['http_status'] <= 599
        sha = row['answer_sha256']
        assert sha is None or type(sha) is str and len(sha) == 64 and all(c in '0123456789abcdef' for c in sha)
        assert row['arithmetic_exact'] is None or type(row['arithmetic_exact']) is bool
        if i < len(records):
            assert row['outcome'] == 'returned_unscored'
    assert packet['attempted_requests'] == sum(r['transport_called'] for r in records)
    complete = len(records) == 2 and all(r['outcome'] == 'returned_unscored' for r in records)
    assert (packet['state'] == 'complete_unscored') == complete
    assert len(json.dumps(packet)) <= 8192
    return packet


def run(*, read_key=key_reader, opener=None, clock=time.monotonic):
    # Resolve key only after the explicit runner invocation. Never print it.
    key = read_key()
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    return validate_packet(capture(transport_for(key, opener), clock))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-authorized', action='store_true')
    args = parser.parse_args()
    if not args.run_authorized:
        print(json.dumps({'state': 'disabled', 'requests': 0}))
        return 0
    packet = run()
    # Deliberate exit 0 for both capture states: the host durably fsyncs the
    # validated packet BEFORE converting state=failed into trial failure.
    print(json.dumps(packet, sort_keys=True, separators=(',', ':')), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
