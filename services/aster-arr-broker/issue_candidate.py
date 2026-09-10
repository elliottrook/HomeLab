#!/usr/bin/env python3
"""Issue one opaque candidate from a strictly eligible Radarr queue record.

The Radarr key is read and used only inside the existing Radarr container.  It
is neither printed nor written to the broker's state or environment.
"""

from __future__ import annotations

import json
import grp
import pwd
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from broker import Candidate
from persistence import state_lock
from state import issue_candidate, store_candidates


STATE_PATH = "/mnt/Media/data/tools/aster-arr-broker/state/candidates.json"
LOCK_PATH = "/mnt/Media/data/tools/aster-arr-broker/state/broker.lock"
MINIMUM_STALE_AGE = timedelta(hours=1)
BROKER_ACCOUNT = "aster-arr-broker"


def eligible_queue_id(payload: object, *, now: datetime) -> int | None:
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        return None
    eligible = []
    for record in payload["records"]:
        if not isinstance(record, dict):
            continue
        queue_id = record.get("id")
        if (
            not isinstance(queue_id, int)
            or isinstance(queue_id, bool)
            or record.get("status") != "completed"
            or record.get("trackedDownloadState") not in {"imported", "ignored"}
        ):
            continue
        try:
            added = datetime.fromisoformat(str(record.get("added")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if added.tzinfo is None or added.astimezone(timezone.utc) > now:
            continue
        if now - added.astimezone(timezone.utc) >= MINIMUM_STALE_AGE:
            eligible.append(queue_id)
    # An opaque reference is safe only when the producer found one
    # unambiguous candidate. Multiple eligible records require a separate
    # operator review and must not become an implicit bulk/first-match choice.
    return eligible[0] if len(eligible) == 1 else None


def radarr_queue() -> object:
    command = (
        'key=$(sed -n "s:.*<ApiKey>\\(.*\\)</ApiKey>.*:\\1:p" /config/config.xml | head -n 1); '
        'test -n "$key"; '
        'curl -fsS -H "X-Api-Key: $key" '
        '"http://127.0.0.1:7878/api/v3/queue?includeMovie=false&page=1&pageSize=1000"'
    )
    completed = subprocess.run(
        ("docker", "exec", "radarr", "sh", "-c", command),
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(completed.stdout)


def store_candidate_state(candidates: list[Candidate]) -> None:
    account = pwd.getpwnam(BROKER_ACCOUNT)
    group = grp.getgrnam(BROKER_ACCOUNT)
    owner = (account.pw_uid, group.gr_gid)
    with state_lock(Path(LOCK_PATH), owner=owner):
        store_candidates(
            Path(STATE_PATH),
            candidates,
            mode=0o640,
            owner=owner,
        )


def main() -> int:
    now = datetime.now(timezone.utc)
    try:
        queue_id = eligible_queue_id(radarr_queue(), now=now)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError, TypeError, ValueError):
        try:
            store_candidate_state([])
        except (KeyError, OSError):
            pass
        print('{"status":"unavailable"}')
        return 1
    if queue_id is None:
        try:
            store_candidate_state([])
        except (KeyError, OSError):
            print('{"status":"unavailable"}')
            return 1
        print('{"status":"none"}')
        return 0
    candidate = issue_candidate(queue_id, now=now)
    try:
        store_candidate_state([candidate])
    except (KeyError, OSError):
        print('{"status":"unavailable"}')
        return 1
    print(json.dumps({"status": "issued", "candidate_ref": candidate.reference, "expires_at": candidate.expires_at.isoformat().replace("+00:00", "Z")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
