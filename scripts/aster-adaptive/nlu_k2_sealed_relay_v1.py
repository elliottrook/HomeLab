"""One-transaction loopback relay for the K2 sealed evaluation."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

import nlu_k2_sealed_evaluation_runner_v1 as evaluation_runner
import nlu_k2_shortlist_arbitrator_v1 as adapter
from nlu_threshold_policy import decode_unique_json


BIND_HOST = "127.0.0.1"
BIND_PORT = 11438
UPSTREAM_ENDPOINT = "http://127.0.0.1:11439/v1/chat/completions"
PATH = "/v1/chat/completions"
REQUESTS = 32
MAX_REQUEST = 65_536
MAX_RESPONSE = 65_536
DEADLINE_SECONDS = 1_800


class RelayError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _validate_token(value: str, name: str) -> None:
    if (not isinstance(value, str) or not 32 <= len(value) <= 256
            or any(not 33 <= ord(character) <= 126 for character in value)):
        raise ValueError(f"invalid {name} credential")


def validate_payload(raw: bytes) -> bytes:
    if not 1 <= len(raw) <= MAX_REQUEST:
        raise ValueError("relay request size changed")
    value = decode_unique_json(raw)
    required = {"model", "temperature", "seed", "stream", "max_tokens",
                "messages", "response_format"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("relay request fields changed")
    messages = value.get("messages")
    response_format = value.get("response_format")
    schema = (response_format.get("schema")
              if isinstance(response_format, dict) else None)
    properties = schema.get("properties") if isinstance(schema, dict) else None
    label = properties.get("label_id") if isinstance(properties, dict) else None
    shortlist = label.get("enum") if isinstance(label, dict) else None
    if (not isinstance(messages, list) or len(messages) != 2
            or not isinstance(messages[1], dict)
            or set(messages[1]) != {"role", "content"}
            or messages[1].get("role") != "user"
            or not isinstance(messages[1].get("content"), str)):
        raise ValueError("relay request messages changed")
    expected = adapter.build_payload(messages[1]["content"], shortlist)
    if raw != expected:
        raise ValueError("relay request is outside exact K2 payload")
    return raw


def forward(raw: bytes, upstream_token: str, *, opener=None) -> bytes:
    validate_payload(raw)
    _validate_token(upstream_token, "upstream")
    transport = opener or urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(
        UPSTREAM_ENDPOINT, data=raw, method="POST",
        headers={"Authorization": "Bearer " + upstream_token,
                 "Content-Type": "application/json"})
    try:
        with transport.open(request, timeout=45) as response:
            result = response.read(MAX_RESPONSE + 1)
            status = response.status
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise RelayError("upstream unavailable") from exc
    if status != 200 or len(result) > MAX_RESPONSE:
        raise RelayError("upstream response failed boundary")
    return evaluation_runner._normalize_response(result)


class State:
    def __init__(self, relay_token: str, upstream_token: str, opener=None):
        _validate_token(relay_token, "relay")
        _validate_token(upstream_token, "upstream")
        self.relay_token = relay_token
        self.upstream_token = upstream_token
        self.opener = opener
        self.requests = 0
        self.failure: str | None = None


def handler_for(state: State):
    class Handler(BaseHTTPRequestHandler):
        server_version = "aster-k2-sealed-relay-v1"
        sys_version = ""

        def log_message(self, _format, *_args):
            return

        def _fixed_error(self, status: int, code: str) -> None:
            body = (json.dumps({"state": "no_go", "code": code},
                               sort_keys=True, separators=(",", ":"))
                    + "\n").encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)

        def _reject_method(self):
            if state.failure is None:
                state.failure = "method_invalid"
            self._fixed_error(405, state.failure)

        do_GET = _reject_method
        do_PUT = _reject_method
        do_DELETE = _reject_method
        do_PATCH = _reject_method
        do_HEAD = _reject_method

        def do_POST(self):
            if state.failure is not None or state.requests >= REQUESTS:
                self._fixed_error(409, "relay_terminal")
                return
            if self.path != PATH:
                state.failure = "path_invalid"
                self._fixed_error(404, state.failure)
                return
            if self.headers.get("Authorization") != "Bearer " + state.relay_token:
                state.failure = "relay_auth_invalid"
                self._fixed_error(403, state.failure)
                return
            if self.headers.get_content_type() != "application/json":
                state.failure = "content_type_invalid"
                self._fixed_error(415, state.failure)
                return
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                length = -1
            if not 1 <= length <= MAX_REQUEST:
                state.failure = "request_size_invalid"
                self._fixed_error(400, state.failure)
                return
            raw = self.rfile.read(length)
            try:
                result = forward(raw, state.upstream_token, opener=state.opener)
            except (RelayError, UnicodeError, json.JSONDecodeError,
                    TypeError, ValueError):
                state.failure = "request_or_upstream_invalid"
                self._fixed_error(502, state.failure)
                return
            state.requests += 1
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(result)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(result)

    return Handler


def _read_token(path: Path, name: str) -> str:
    value = path.read_text().splitlines()[0].strip()
    _validate_token(value, name)
    return value


def serve(relay_token: str, upstream_token: str, *,
          server_factory=HTTPServer, clock=time.monotonic) -> dict[str, object]:
    state = State(relay_token, upstream_token)
    server = server_factory((BIND_HOST, BIND_PORT), handler_for(state))
    server.timeout = 1
    end = clock() + DEADLINE_SECONDS
    try:
        while state.requests < REQUESTS and state.failure is None and clock() < end:
            server.handle_request()
    finally:
        server.server_close()
    complete = state.requests == REQUESTS and state.failure is None
    return {"schema": "aster-nlu-k2-sealed-relay-summary.v1",
            "state": "complete" if complete else "no_go",
            "requests": state.requests, "retries": 0,
            "failure_code": state.failure or (None if complete else "deadline"),
            "authority": "not-granted"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--relay-token-file", type=Path, required=True)
    parser.add_argument("--upstream-token-file", type=Path, required=True)
    args = parser.parse_args()
    result = serve(_read_token(args.relay_token_file, "relay"),
                   _read_token(args.upstream_token_file, "upstream"))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["state"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
