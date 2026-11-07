#!/usr/bin/env python3
"""Content-silent health summary for HomeLab Doctor integration."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def probe(name: str, url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"name": name, "ok": 200 <= response.status < 300, "status": response.status}
    except urllib.error.HTTPError as error:
        return {"name": name, "ok": False, "status": error.code}
    except (urllib.error.URLError, TimeoutError):
        return {"name": name, "ok": False, "status": "unreachable"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--romm", default="http://127.0.0.1:8080/api/heartbeat")
    parser.add_argument("--romarr", default="http://127.0.0.1:6868/api/health")
    parser.add_argument("--broker", default="http://127.0.0.1:8099/health")
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    results = [
        probe("romm", args.romm, args.timeout),
        probe("romarr", args.romarr, args.timeout),
        probe("broker", args.broker, args.timeout),
    ]
    output = {"ok": all(result["ok"] for result in results), "services": results}
    print(json.dumps(output, sort_keys=True))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

