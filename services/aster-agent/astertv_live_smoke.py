#!/usr/bin/env python3
"""Exercise the live AsterTV route without emitting its credential."""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


URL = "http://192.168.70.10:9120/v1/astertv/intent"


def call(key, payload):
    request = urllib.request.Request(
        URL, json.dumps(payload).encode(), {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            "X-AsterTV-Client": "AsterTV-Jen",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, None


key = os.environ.get("ASTER_TV_API_KEY", "")
if not key:
    raise SystemExit("missing-astertv-key")
now = datetime.now(timezone.utc)
base = {
    "request_id": "live-check-1234", "client_id": "AsterTV-Jen",
    "room_id": "jen-lab", "profile_id": "jason", "origin_page": "media",
    "utterance": "show me films about space", "issued_at": now.isoformat(),
    "expires_at": (now + timedelta(seconds=15)).isoformat(),
}
wrong, _ = call("wrong", base)
guest, _ = call(key, dict(base, request_id="live-guest-1234", profile_id="guest"))
valid, body = call(key, base)
if not (
    wrong == 401 and guest == 403 and valid == 200
    and body["intent"] == "media.search"
    and body["arguments"] == {"query": "films about space"}
):
    raise SystemExit("live-smoke-failed")
print(json.dumps({
    "wrong_key": wrong, "guest": guest, "valid": valid,
    "intent": body["intent"], "credential_output": False,
}, sort_keys=True))
