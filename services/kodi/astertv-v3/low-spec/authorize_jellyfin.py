#!/usr/bin/env python3
"""Authorize AsterTV-Jen Quick Connect with the existing Family user session."""

import json
import os
from pathlib import Path
import socket
import urllib.parse
import urllib.request


QC = Path("/storage/.aster-staging/jellyfin-quick-connect.json")
FAMILY = Path("/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/data.json")
SERVER = "http://192.168.20.40:8096"


def main() -> None:
    if socket.gethostname() != "AsterTV-Family" or os.getuid() != 0:
        raise SystemExit("AsterTV-Family-root-only")
    qc = json.loads(QC.read_text())
    servers = json.loads(FAMILY.read_text()).get("Servers", [])
    if len(servers) != 1 or not isinstance(servers[0].get("AccessToken"), str):
        raise RuntimeError("family-jellyfin-session-schema")
    token = servers[0]["AccessToken"]
    auth = ("MediaBrowser Client=AsterTV%20Provisioner, Device=AsterTV-Family, "
            "DeviceId=AsterTV-Family, Version=1, Token="
            + urllib.parse.quote(token, safe=""))
    req = urllib.request.Request(
        SERVER + "/QuickConnect/Authorize?Code="
        + urllib.parse.quote(qc["Code"], safe=""), data=b"{}", method="POST",
        headers={"Authorization": auth, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("jellyfin-quick-connect-authorize")
    QC.unlink()
    print(json.dumps({"authorized": True, "credential_output": False}, sort_keys=True))


if __name__ == "__main__":
    main()
