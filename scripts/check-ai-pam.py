#!/usr/bin/env python3
"""Read-only, non-secret AI-PAM health and policy-drift check for Doctor."""

from __future__ import annotations

import base64
import json
import shlex
import subprocess
import sys
import time


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
RESTORE_TESTED_AT = 1_790_276_400
MAX_RESTORE_AGE_SECONDS = 366 * 86_400
MAX_BACKUP_AGE_SECONDS = 36 * 3_600
MAX_AUDIT_AGE_SECONDS = 45 * 86_400

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
 "services":db.execute("SELECT service_id,enabled,rotation_due FROM services ORDER BY service_id").fetchall(),
 "capabilities":db.execute("SELECT capability,service_id,risk_class,enabled FROM capabilities ORDER BY capability").fetchall(),
 "agents":db.execute("SELECT agent_id,state FROM agents ORDER BY agent_id").fetchall(),
 "active_requests":db.execute("SELECT count(*) FROM requests WHERE status IN ('pending','approved')").fetchone()[0],
 "expired_active":db.execute("SELECT count(*) FROM requests WHERE status IN ('pending','approved') AND expires_at<=?",(now,)).fetchone()[0],
 "audit":db.execute("SELECT COALESCE(MAX(occurred_at),0),COUNT(*) FROM audit").fetchone(),
 "outcomes":db.execute("SELECT status,COUNT(*) FROM requests GROUP BY status ORDER BY status").fetchall(),
 "services_active":{u:active(u) for u in ["homelab-broker.service","homelab-broker-approval.service",
   "forgejo-mcp-gateway.service","forgejo-mcp-write-gateway.service","aster-lab-operations-broker.service"]},
 "sockets":{p:socket_shape(p) for p in ["/run/homelab-broker/mcp.sock","/run/homelab-broker/approval.sock",
   "/run/homelab-forgejo-mcp/gateway.sock","/run/homelab-forgejo-mcp-write/gateway.sock",
   "/run/aster-lab-operations-broker/gateway.sock"]},
}
db.close()
try:
    with urllib.request.urlopen("https://auth.elliottrook.com/application/o/aster-companion/.well-known/openid-configuration",timeout=5) as response:
        discovery=json.load(response)
    data["authentik"]={"reachable":True,"issuer":discovery.get("issuer")}
except Exception:
    data["authentik"]={"reachable":False,"issuer":None}
try:
    context=ssl.create_default_context(cafile="/etc/homelab-broker/openbao-ca.crt")
    with urllib.request.urlopen("https://192.168.50.24:8200/v1/sys/health",context=context,timeout=5) as response:
        health=json.load(response)
    data["openbao"]={"reachable":True,"sealed":health.get("sealed"),"initialized":health.get("initialized")}
except Exception:
    data["openbao"]={"reachable":False,"sealed":None,"initialized":None}
print(json.dumps(data,separators=(",",":")))
'''

HOST_CODE = r'''import glob,json,os,time
def newest(vmid):
    paths=glob.glob(f"/mnt/backups/dump/vzdump-lxc-{vmid}-*.tar.zst")
    return max((os.path.getmtime(path) for path in paths),default=0)
print(json.dumps({"now":int(time.time()),"backups":{"104":newest(104),"117":newest(117)}}))
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
    now = int(data.get("now", time.time()))
    for row in data.get("services", []):
        rotation = row[2] if len(row) > 2 else ""
        if rotation not in {"operator-managed", "not-applicable"}:
            try:
                due = int(time.mktime(time.strptime(rotation, "%Y-%m-%d")))
            except (TypeError, ValueError):
                failures.append("invalid rotation metadata")
            else:
                if due < now:
                    failures.append("overdue credential rotation")

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
    audit = data.get("audit", [0, 0])
    if len(audit) != 2 or not audit[1] or now - int(audit[0]) > MAX_AUDIT_AGE_SECONDS:
        failures.append("audit missing or stale")
    if not all(data.get("services_active", {}).values()):
        failures.append("service unit inactive")

    sockets = data.get("sockets", {})
    if not sockets or any(not value or not value.get("socket") or value.get("mode") not in {0o600, 0o660}
                          for value in sockets.values()):
        failures.append("socket permission/readiness drift")

    openbao = data.get("openbao", {})
    if not openbao.get("reachable") or openbao.get("sealed") is not False or openbao.get("initialized") is not True:
        failures.append("OpenBao unavailable or sealed")
    authentik = data.get("authentik", {})
    if not authentik.get("reachable") or authentik.get("issuer") != "https://auth.elliottrook.com/application/o/aster-companion/":
        failures.append("Authentik discovery unavailable or drifted")
    backups = data.get("backups", {})
    if any(now - int(backups.get(vmid, 0)) > MAX_BACKUP_AGE_SECONDS for vmid in ("104", "117")):
        failures.append("AI-PAM guest backup stale")
    if now - RESTORE_TESTED_AT > MAX_RESTORE_AGE_SECONDS:
        failures.append("isolated restore evidence stale")

    if failures:
        return 1, "AI-PAM unhealthy: " + ", ".join(failures)
    outcomes = sum(int(row[1]) for row in data.get("outcomes", []))
    return 0, (f"AI-PAM healthy; policy catalogue exact, Authentik reachable, OpenBao unsealed, "
               f"backups/restore current, {data.get('active_requests', 0)} active request(s), {outcomes} recorded outcome(s)")


def collect() -> dict:
    encoded = base64.b64encode(REMOTE_CODE.encode()).decode()
    guest = f"pct exec 104 -- python3 -c {shlex.quote(f'import base64;exec(base64.b64decode({encoded!r}))')}"
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "root@192.168.50.10", guest],
        capture_output=True, text=True, timeout=25, check=True,
    )
    data = json.loads(result.stdout)
    host_encoded = base64.b64encode(HOST_CODE.encode()).decode()
    host_result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "root@192.168.50.10",
         "python3 -c " + shlex.quote(f"import base64;exec(base64.b64decode({host_encoded!r}))")],
        capture_output=True, text=True, timeout=15, check=True,
    )
    data.update(json.loads(host_result.stdout))
    return data


def main() -> int:
    try:
        code, message = classify(collect())
    except Exception:
        code, message = 1, "AI-PAM health could not be verified"
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
