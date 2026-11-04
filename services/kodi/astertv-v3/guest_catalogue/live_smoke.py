#!/usr/bin/env python3
"""Sanitized Jen smoke preparation and history comparison."""

import argparse
import json
import socket
import time
import urllib.parse
import urllib.request
from pathlib import Path


CREDENTIAL = Path("/storage/.aster-private/jellyfin-guest.json")
STATE = Path("/storage/.aster-staging/astertv-guest-smoke-item.json")


def auth():
    value = json.loads(CREDENTIAL.read_text())
    authorization = (
        "MediaBrowser Client=AsterTV Guest, Device=AsterTV-Jen, DeviceId="
        + value["device_id"] + ", Version=1, Token=" + value["access_token"]
    )
    return value, {"Authorization": authorization, "X-Emby-Token": value["access_token"]}


def get(value, headers, path):
    request = urllib.request.Request(value["server_url"] + path, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def prepare():
    for _ in range(30):
        try:
            connection = socket.create_connection(("127.0.0.1", 57321), 1)
            connection.close(); break
        except OSError:
            time.sleep(0.5)
    else:
        raise SystemExit("guest-proxy-not-listening")
    value, headers = auth()
    movie = next(row for row in value["allowed_folders"] if row["name"] == "Movies")
    query = urllib.parse.urlencode({"ParentId": movie["id"], "Recursive": "true",
                                    "IncludeItemTypes": "Movie", "Limit": 1})
    rows = get(value, headers, "/Users/" + value["user_id"] + "/Items?" + query)["Items"]
    if len(rows) != 1:
        raise SystemExit("movie-fixture-cardinality")
    row = rows[0]; history = row.get("UserData") or {}
    STATE.write_text(json.dumps({"id": row["Id"], "history_before": history}))
    print(json.dumps({"proxy_listening": True, "movie_id": row["Id"],
                      "history_before": {"played": history.get("Played", False),
                                         "position": history.get("PlaybackPositionTicks", 0)},
                      "credential_output": False}, sort_keys=True))


def compare():
    state = json.loads(STATE.read_text()); value, headers = auth()
    row = get(value, headers, "/Users/" + value["user_id"] + "/Items/" + state["id"])
    before = state["history_before"]; after = row.get("UserData") or {}
    keys = ("Played", "PlaybackPositionTicks", "PlayCount", "LastPlayedDate")
    unchanged = all(before.get(key) == after.get(key) for key in keys)
    print(json.dumps({"guest_history_unchanged": unchanged, "credential_output": False},
                     sort_keys=True))
    if not unchanged:
        raise SystemExit("guest-history-changed")


parser = argparse.ArgumentParser(); parser.add_argument("action", choices=("prepare", "compare"))
args = parser.parse_args(); {"prepare": prepare, "compare": compare}[args.action]()
