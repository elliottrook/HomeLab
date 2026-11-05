#!/usr/bin/env python3
"""Content-free health probe for the private Aster Remote deployment."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess


CLIENTS = (
    ("AsterTV-Jen", "192.168.1.180", "jen-lab"),
    ("AsterTV-Family", "192.168.1.157", "family"),
    ("AsterTV-Bedroom", "192.168.1.140", "bedroom"),
)
SSH = ("ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5")
PINNED_HOSTS = (
    Path(__file__).resolve().parents[1]
    / "services/kodi/astertv-v2/reconciliation/payload/home-delivery/known_hosts"
)

CLIENT_PROBE = r'''
import hashlib,json,os,pathlib,socket,subprocess
host=socket.gethostname()
stable=pathlib.Path("/storage/.aster-v3/m8" if host=="AsterTV-Jen" else "/storage/.aster-v3/m8-remote")
live=pathlib.Path("/storage/.kodi/addons/service.asterremote")
def tree(path):
 h=hashlib.sha256()
 for p in sorted(x for x in path.rglob("*") if x.is_file()):
  h.update(str(p.relative_to(path)).encode()+b"\0");h.update(p.read_bytes())
 return h.hexdigest()
def rpc(method,params=None):
 q={"jsonrpc":"2.0","id":1,"method":method}
 if params is not None:q["params"]=params
 with socket.create_connection(("127.0.0.1",9090),3) as s:
  s.sendall((json.dumps(q)+"\r\n").encode());return json.loads(s.recv(65536)).get("result",{})
key=pathlib.Path("/storage/.aster-private/asterremote-client.key")
config=pathlib.Path("/storage/.aster-private/asterremote-client.json")
manifest=json.loads((stable/"manifest.json").read_text())
print(json.dumps({"host":host,"kodi":subprocess.run(["systemctl","is-active","kodi"],capture_output=True,text=True).stdout.strip(),
 "addon":rpc("Addons.GetAddonDetails",{"addonid":"service.asterremote","properties":["enabled"]}).get("addon",{}).get("enabled"),
 "idle":not bool(rpc("Player.GetActivePlayers")),"key_mode":oct(key.stat().st_mode&0o777),
 "config_mode":oct(config.stat().st_mode&0o777) if config.exists() else "jen-default",
 "live_stable":tree(live)==tree(stable/"service.asterremote"),
 "manifest":manifest=={"schema":1,"addon_sha256":tree(stable/"service.asterremote")}}))
'''

GATEWAY_PROBE = r'''
import json,subprocess,urllib.error,urllib.request
values={}
for line in open("/etc/aster/asterremote.env"):
 if "=" in line:
  key,value=line.rstrip().split("=",1);values[key]=value
clients=json.loads(values["ASTER_REMOTE_CLIENTS"]);subjects=json.loads(values["ASTER_REMOTE_SUBJECT_ROOMS"])
def status(path):
 try:
  return urllib.request.urlopen("http://192.168.70.10:9120"+path,timeout=3).status
 except urllib.error.HTTPError as error:return error.code
print(json.dumps({"agent":subprocess.run(["systemctl","is-active","aster-agent"],capture_output=True,text=True).stdout.strip(),
 "remote":status("/remote/"),"denial":status("/v1/remote/session"),
 "clients":sorted((key,row["room_id"]) for key,row in clients.items()),
 "rooms":sorted(next(iter(subjects.values()))),"subject_count":len(subjects),
 "keys_present":all(bool(row.get("key")) for row in clients.values())}))
'''


def command(args, *, input_text=None):
    result = subprocess.run(args, input=input_text, text=True, capture_output=True, timeout=20)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip())
    return result.stdout.strip()


def validate_gateway(row):
    expected = sorted((host, room) for host, _ip, room in CLIENTS)
    if not (
        row.get("agent") == "active" and row.get("remote") == 200
        and row.get("denial") == 401 and row.get("clients") == [list(item) for item in expected]
        and row.get("rooms") == sorted(room for _host, _ip, room in CLIENTS)
        and row.get("subject_count") == 1 and row.get("keys_present") is True
    ):
        raise RuntimeError("gateway identity, route or denial drift")


def validate_client(row, host):
    if not (
        row.get("host") == host and row.get("kodi") == "active"
        and row.get("addon") is True and row.get("key_mode") == "0o600"
        and row.get("config_mode") in {"0o600", "jen-default"}
        and row.get("live_stable") is True and row.get("manifest") is True
    ):
        raise RuntimeError(host + " client, custody or manifest drift")


def main():
    gateway = json.loads(command(
        SSH + ("proxmox", "pct", "exec", "104", "--", "python3", "-"),
        input_text=GATEWAY_PROBE,
    ))
    validate_gateway(gateway)
    for host, ip, _room in CLIENTS:
        transport = SSH
        if host != "AsterTV-Jen":
            transport += ("-o", "UserKnownHostsFile=" + str(PINNED_HOSTS))
        row = json.loads(command(transport + ("root@" + ip, "python3", "-"), input_text=CLIENT_PROBE))
        validate_client(row, host)
    print("Aster Remote gateway, three room identities, clients and manifests are healthy")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Aster Remote unhealthy: " + str(error))
        raise SystemExit(1)
