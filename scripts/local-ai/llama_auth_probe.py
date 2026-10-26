"""Guest-local production llama authentication probe; never prints keys."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

KEY_PATH = "/etc/aster-llama-api-keys"
URL = "http://192.168.70.12:11435/v1/models"
EXPECTED_MODEL = "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(request.full_url, code, msg, headers, fp)


def _request(opener, authorization=None):
    headers = {} if authorization is None else {"Authorization": authorization}
    request = urllib.request.Request(URL, headers=headers)
    try:
        with opener.open(request, timeout=5) as response:
            return response.status, json.loads(response.read(65536)), request
    except urllib.error.HTTPError as exc:
        return exc.code, None, request


def probe() -> bool:
    with open(KEY_PATH, encoding="ascii") as stream:
        keys = [line.strip() for line in stream if line.strip()]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        unauthenticated, _payload, _request_value = _request(opener)
        invalid, _payload, _request_value = _request(
            opener, "Bearer aster-fixed-invalid-probe"
        )
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False
    if unauthenticated != 401 or invalid != 401:
        return False
    for key in keys:
        try:
            status, payload, _request_value = _request(opener, "Bearer " + key)
            models = payload.get("data")
            if status == 200 and isinstance(models, list) and any(
                isinstance(model, dict) and model.get("id") == EXPECTED_MODEL
                for model in models
            ):
                return True
        except (urllib.error.URLError, TimeoutError, ValueError, AttributeError):
            continue
    return False


if __name__ == "__main__":
    raise SystemExit(0 if probe() else 1)
