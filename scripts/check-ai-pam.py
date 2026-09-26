#!/usr/bin/env python3
"""Read-only, non-secret AI-PAM health and policy-drift check for Doctor."""

from __future__ import annotations

import base64
import json
import shlex
import subprocess
import sys


EXPECTED_CAPABILITIES = {
    "broker.health.read": ("synthetic", "green"),
    "broker.root-material": ("synthetic", "black"),
    "broker.synthetic.network-change": ("synthetic", "red"),
    "broker.synthetic.restart": ("synthetic", "yellow"),
    "forgejo.read.repository": ("forgejo-mcp", "green"),
    "forgejo.write.safe-branch": ("forgejo-mcp-safe-write", "yellow"),
    "lab.doctor.latest": ("lab-operations", "green"),
    "lab.doctor.run": ("lab-operations", "yellow"),
}
EXPECTED_SERVICES = {
    "forgejo-mcp",
    "forgejo-mcp-safe-write",
    "lab-operations",
    "synthetic",
}

REMOTE_CODE = r'''import json,os,socket,sqlite3,stat,ssl,subprocess,time,urllib.request

def active(unit):
    return subprocess.run(["systemctl","is-active","--quiet",unit]).returncode == 0

def socket_shape(path):
    try:
        value=os.stat(path)
        return {"socket":stat.S_ISSOCK(value.st_mode),"mode":stat.S_IMODE(value.st_mode),
                "uid":value.st_uid,"gid":value.st_gid}
    except OSError:
        return None

db=sqlite3.connect("file:/var/lib/homelab-broker/broker.db?mode=ro",uri=True,timeout=5)
now=int(time.time())
data={
 "integrity":db.execute("PRAGMA integrity_check").fetchone()[0],
 "global_enabled":db.execute("SELECT value FROM settings WHERE key='global_enabled'").fetchone()[0],
 "services":db.execute("SELECT service_id,enabled FROM services ORDER BY service_id").fetchall(),
 "capabilities":db.execute("SELECT capability,service_id,risk_class,enabled FROM capabilities ORDER BY capability").fetchall(),
 "agents":db.execute("SELECT agent_id,state FROM agents ORDER BY agent_id").fetchall(),
 "active_requests":db.execute("SELECT count(*) FROM requests WHERE status IN ('pending','approved')").fetchone()[0],
 "expired_active":db.execute("SELECT count(*) FROM requests WHERE status IN ('pending','approved') AND expires_at<=?",(now,)).fetchone()[0],
 "services_active":{u:active(u) for u in ["homelab-broker.service","homelab-broker-approval.service",
   "forgejo-mcp-gateway.service","forgejo-mcp-write-gateway.service","aster-lab-operations-broker.service"]},
 "sockets":{p:socket_shape(p) for p in ["/run/homelab-broker/mcp.sock","/run/homelab-broker/approval.sock",
   "/run/homelab-forgejo-mcp/gateway.sock","/run/homelab-forgejo-mcp-write/gateway.sock",
   "/run/aster-lab-operations-broker/gateway.sock"]},
}
db.close()
try:
    context=ssl.create_default_context(cafile="/etc/homelab-broker/openbao-ca.crt")
    with urllib.request.urlopen("https://192.168.50.24:8200/v1/sys/health",context=context,timeout=5) as response:
        health=json.load(response)
    data["openbao"]={"reachable":True,"sealed":health.get("sealed"),"initialized":health.get("initialized")}
except Exception:
    data["openbao"]={"reachable":False,"sealed":None,"initialized":None}
print(json.dumps(data,separators=(",",":")))
'''


def classify(data: dict) -> tuple[int, str]:
    failures: list[str] = []
    if data.get("integrity") != "ok":
        failures.append("database integrity")
    if data.get("global_enabled") != "1":
        failures.append("global access disabled")

    services = {row[0]: (row[1] == 1) for row in data.get("services", [])}
    if set(services) != EXPECTED_SERVICES or not all(services.values()):
        failures.append("service catalogue drift")

    capabilities = {row[0]: (row[1], row[2], row[3] == 1) for row in data.get("capabilities", [])}
    expected = {name: (*shape, True) for name, shape in EXPECTED_CAPABILITIES.items()}
    if capabilities != expected:
        failures.append("capability catalogue drift")

    agents = dict(data.get("agents", []))
    if agents.get("agent-hermes") != "operator":
        failures.append("agent-hermes lifecycle drift")
    if any(state not in {"operator", "retired"} for state in agents.values()):
        failures.append("unexpected active agent state")
    if data.get("expired_active"):
        failures.append("expired active requests")
    if not all(data.get("services_active", {}).values()):
        failures.append("service unit inactive")

    sockets = data.get("sockets", {})
    if not sockets or any(not value or not value.get("socket") or value.get("mode") not in {0o600, 0o660}
                          for value in sockets.values()):
        failures.append("socket permission/readiness drift")

    openbao = data.get("openbao", {})
    if not openbao.get("reachable") or openbao.get("sealed") is not False or openbao.get("initialized") is not True:
        failures.append("OpenBao unavailable or sealed")

    if failures:
        return 1, "AI-PAM unhealthy: " + ", ".join(failures)
    return 0, f"AI-PAM healthy; policy catalogue exact, OpenBao unsealed, {data.get('active_requests', 0)} active request(s)"


def collect() -> dict:
    encoded = base64.b64encode(REMOTE_CODE.encode()).decode()
    guest = f"pct exec 104 -- python3 -c {shlex.quote(f'import base64;exec(base64.b64decode({encoded!r}))')}"
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "root@192.168.50.10", guest],
        capture_output=True, text=True, timeout=25, check=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    try:
        code, message = classify(collect())
    except Exception:
        code, message = 1, "AI-PAM health could not be verified"
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
