"""One-attempt, no-tool A1 client adapter for an admitted isolated gateway.

This module neither obtains lab authority nor starts a run. The caller must
validate a live lease and journal each attempt before calling ``invoke``.
Only fictional A1 cases and a test-scoped ingress credential belong here.
"""
from __future__ import annotations

import ipaddress
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from aster_full_path_request import wire_bytes_for
from client_display_clock import ClientDisplayClock

OBSERVATION_ID = re.compile(r"[0-9a-f]{32}\Z")
MAX_RESPONSE = 65_536
LOCAL_NETWORKS = tuple(ipaddress.ip_network(value) for value in
                       ("127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))


class A1TransportError(Exception):
    """Content-free terminal failure; never include URL, token or answer."""

    def __init__(self, code: str, timing: dict):
        super().__init__(code)
        self.timing = timing


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _endpoint(url: str) -> str:
    if not isinstance(url, str):
        raise ValueError("invalid isolated endpoint")
    parsed = urllib.parse.urlsplit(url)
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except (ValueError, TypeError):
        raise ValueError("invalid isolated endpoint") from None
    if (parsed.scheme != "http" or not isinstance(address, ipaddress.IPv4Address)
            or not any(address in network for network in LOCAL_NETWORKS)
            or parsed.username or parsed.password or port is None
            or not 1 <= port <= 65535
            or parsed.path != "/v1/chat/completions"
            or parsed.query or parsed.fragment):
        raise ValueError("invalid isolated endpoint")
    return url


def invoke(case: dict, *, endpoint: str, ingress_token: bytes,
           opener=None, clock=None, timeout_s: float = 60) -> tuple[str, ClientDisplayClock]:
    """Return a bounded answer and a pending content-free client clock.

    The caller must finish the returned clock only after its final private
    answer-capture/display boundary is durable. A failure after send is
    uncertain and must not be retried under the same run directory.
    """
    url = _endpoint(endpoint)
    if (not isinstance(ingress_token, bytes)
            or not 16 <= len(ingress_token) <= 256
            or any(not 33 <= byte <= 126 for byte in ingress_token)):
        raise ValueError("invalid test credential")
    if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float))
            or not 0 < timeout_s <= 60):
        raise ValueError("invalid bounded request timeout")
    body = wire_bytes_for(case)
    client = ClientDisplayClock(clock=clock) if clock is not None else ClientDisplayClock()
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + ingress_token.decode("ascii")},
    )
    transport = opener if opener is not None else urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with transport.open(request, timeout=timeout_s) as response:
            status = response.status
            identity = response.headers.get("X-Aster-Observation-Id")
            raw = response.read(MAX_RESPONSE + 1)
    except (urllib.error.URLError, TimeoutError, OSError):
        raise A1TransportError("unavailable_or_uncertain",
                               client.finish(terminal_displayed=False)) from None
    if (isinstance(identity, str) and OBSERVATION_ID.fullmatch(identity)
            and type(status) is int and 100 <= status <= 599):
        client.response_identity(identity, status)
    if (status != 200 or not isinstance(identity, str)
            or not OBSERVATION_ID.fullmatch(identity) or len(raw) > MAX_RESPONSE):
        raise A1TransportError("invalid_or_uncertain_response",
                               client.finish(terminal_displayed=False))
    try:
        payload = json.loads(raw)
        choices = payload["choices"]
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError
        choice = choices[0]
        answer = choice["message"]["content"]
        if (choice["finish_reason"] != "stop" or not isinstance(answer, str)
                or not answer.strip() or len(answer.encode("utf-8")) > 16_000):
            raise ValueError
        return answer, client
    except (KeyError, IndexError, TypeError, ValueError, UnicodeError):
        raise A1TransportError("invalid_or_uncertain_response",
                               client.finish(terminal_displayed=False)) from None
