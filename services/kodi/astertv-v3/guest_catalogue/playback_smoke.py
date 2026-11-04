#!/usr/bin/env python3
"""Run one bounded Jen Guest playback smoke and leave playback stopped."""

import json
import argparse
import socket
import time
import urllib.parse
from pathlib import Path


STATE = Path("/storage/.aster-staging/astertv-guest-smoke-item.json")


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        payload = connection.recv(65536)
    value = json.loads(payload)
    if "error" in value:
        raise RuntimeError("json-rpc-error:" + str(value["error"].get("code")))
    return value.get("result")


parser = argparse.ArgumentParser(); parser.add_argument("--direct", action="store_true")
args = parser.parse_args()

if rpc("Player.GetActivePlayers"):
    raise SystemExit("active-playback")
identifier = json.loads(STATE.read_text())["id"]
route = "plugin://plugin.video.asterguest/?" + urllib.parse.urlencode(
    {"action": "play", "item": identifier}
)
if args.direct:
    route = "http://127.0.0.1:57321/stream/" + identifier
rpc("Player.Open", {"item": {"file": route}})
player = None
for _ in range(40):
    active = rpc("Player.GetActivePlayers")
    if active:
        player = active[0]["playerid"]; break
    time.sleep(0.25)
if player is None:
    raise SystemExit("playback-did-not-start")
properties = None
for _ in range(120):
    properties = rpc("Player.GetProperties", {
        "playerid": player, "properties": ["time", "speed", "percentage"]
    })
    if properties["speed"] == 1 and properties["time"]["seconds"] >= 2:
        break
    time.sleep(0.25)
else:
    rpc("Player.Stop", {"playerid": player})
    raise SystemExit("playback-did-not-advance")
rpc("Player.Stop", {"playerid": player})
for _ in range(20):
    if not rpc("Player.GetActivePlayers"):
        break
    time.sleep(0.25)
else:
    raise SystemExit("playback-did-not-stop")
print(json.dumps({"started": True, "stopped": True,
                  "advanced_seconds": properties["time"]["seconds"],
                  "speed": properties["speed"]}, sort_keys=True))
