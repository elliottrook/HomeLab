#!/usr/bin/env python3
"""Content-free live smoke for Jen's owner-approved podcast queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
from urllib.error import HTTPError
from urllib.request import Request, urlopen


CLIENT = Path("/storage/.kodi/userdata/addon_data/script.astertv.podcast.requests/client.json")
STATE = Path("/storage/.aster-staging/aster-podcast-request-smoke.json")
IDEMPOTENCY = "sa_m5p2_" + "x" * 32


def request(base: str, token: str, path: str, value: object | None = None) -> tuple[int, object]:
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    data = None if value is None else json.dumps(value).encode()
    method = "GET" if value is None else "POST"
    query = Request(base + path, headers=headers, data=data, method=method)
    try:
        with urlopen(query, timeout=20) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "verify"))
    args = parser.parse_args()
    if socket.gethostname() != "AsterTV-Jen" or os.getuid() != 0:
        raise SystemExit("AsterTV-Jen-root-only")
    client = json.loads(CLIENT.read_text())
    base, token = client["server_url"], client["token"]
    wrong, _ = request(base, "z" * 48, "/v1/status?request_ref=req_" + "R" * 32)
    if wrong != 401:
        raise RuntimeError("wrong-token-not-denied")
    if args.mode == "create":
        status, found = request(base, token, "/v1/search", {"term": "science", "country": "ca"})
        available = [item for item in found.get("results", [])
                     if item.get("status") == "available_to_request"]
        if status != 200 or not available:
            raise RuntimeError("search-no-candidate")
        candidate_ref = available[0]["candidate_ref"]
        status, created = request(base, token, "/v1/request", {
            "candidate_ref": candidate_ref, "idempotency_key": IDEMPOTENCY, "confirm": True})
        status2, replay = request(base, token, "/v1/request", {
            "candidate_ref": candidate_ref, "idempotency_key": IDEMPOTENCY, "confirm": True})
        if (status, status2) != (200, 200) or created.get("duplicate") is not False \
                or replay.get("duplicate") is not True \
                or created.get("request_ref") != replay.get("request_ref") \
                or created.get("status") != "pending_owner_approval":
            raise RuntimeError("idempotency-smoke")
        payload = {"candidate_ref": candidate_ref, "request_ref": created["request_ref"]}
        descriptor = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump(payload, stream); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        print(json.dumps({"state": "queued-test-only", "search_count": found.get("count"),
                          "wrong_token": wrong, "status": created["status"],
                          "duplicate_replay": True,
                          "request_ref_sha256": hashlib.sha256(created["request_ref"].encode()).hexdigest(),
                          "podcast_created": False}, sort_keys=True))
    else:
        retained = json.loads(STATE.read_text())
        status, current = request(base, token, "/v1/status?request_ref=" + retained["request_ref"])
        status2, replay = request(base, token, "/v1/request", {
            "candidate_ref": retained["candidate_ref"],
            "idempotency_key": IDEMPOTENCY, "confirm": True})
        if status != 200 or status2 != 200 or current.get("status") != "pending_owner_approval" \
                or replay.get("duplicate") is not True \
                or current.get("request_ref") != retained["request_ref"]:
            raise RuntimeError("restart-persistence-smoke")
        print(json.dumps({"state": "restart-persisted", "wrong_token": wrong,
                          "status": current["status"], "duplicate_replay": True,
                          "request_ref_sha256": hashlib.sha256(retained["request_ref"].encode()).hexdigest(),
                          "podcast_created": False}, sort_keys=True))


if __name__ == "__main__":
    main()
