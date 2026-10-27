"""Restricted HTTP transport for confirmed Music and Books requests."""

import json
from pathlib import Path
import urllib.error
import urllib.request


class AcquisitionTransportUnavailable(RuntimeError):
    pass


def post(base, token_path, payload, opener=urllib.request.urlopen):
    if base != "http://192.168.20.40:8788":
        raise AcquisitionTransportUnavailable("acquisition-http-broker-invalid")
    try:
        token = Path(token_path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as error:
        raise AcquisitionTransportUnavailable(
            "acquisition-http-token-unavailable") from error
    if not 32 <= len(token) <= 512 or "\n" in token:
        raise AcquisitionTransportUnavailable("acquisition-http-token-invalid")
    raw = json.dumps(payload, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        base + "/v1/acquisition", data=raw, method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with opener(request, timeout=15) as response:
            body = response.read(8193)
            if response.status != 200 or not 0 < len(body) <= 8192:
                raise AcquisitionTransportUnavailable(
                    "acquisition-http-response-invalid")
            value = json.loads(body)
            if type(value) is not dict:
                raise AcquisitionTransportUnavailable(
                    "acquisition-http-response-invalid")
            return value
    except AcquisitionTransportUnavailable:
        raise
    except (OSError, UnicodeError, urllib.error.URLError,
            urllib.error.HTTPError, json.JSONDecodeError) as error:
        raise AcquisitionTransportUnavailable(
            "acquisition-http-unavailable") from error
