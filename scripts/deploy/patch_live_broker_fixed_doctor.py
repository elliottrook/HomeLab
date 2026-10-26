#!/usr/bin/env python3
"""Generate the fixed-Doctor broker candidate from exact deployed predecessors."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PREDECESSORS = {
    "broker_admin.py": "00216b27e179d936e1b5fd9feb1ca17dc25bb6af3e34b044408ae21133924e8b",
    "broker_service.py": "05a555241b97ad7e6a9d268ad91426af0432fb0ae0785dabf46bf4081e713ccb",
}
CANDIDATES = {
    "broker_admin.py": "e90acd24acfa13f959070f2c791d29ea28ebf1d4240edd5a9b39b54dfc7ef4aa",
    "broker_service.py": "c6217f4988510b4d38581829b4f6b333487b1cd35732a6ba5b3d82dcc69b627e",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--admin-source", required=True, type=Path)
parser.add_argument("--service-source", required=True, type=Path)
parser.add_argument("--output-dir", required=True, type=Path)
args = parser.parse_args()
sources = {
    "broker_admin.py": args.admin_source,
    "broker_service.py": args.service_source,
}
for name, path in sources.items():
    actual = digest(path)
    if actual != PREDECESSORS[name]:
        raise SystemExit(f"{name}: predecessor drift: {actual}")
args.output_dir.mkdir(parents=True, exist_ok=True)
admin = args.output_dir / "broker_admin.py"
service = args.output_dir / "broker_service.py"
admin.write_bytes(args.admin_source.read_bytes())
service.write_bytes(args.service_source.read_bytes())


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"expected one match, found {text.count(old)} for {old[:80]!r}")
    return text.replace(old, new, 1)


text = admin.read_text()
text = replace_once(
    text,
    '    subparsers.add_parser("graduate-lab-doctor")\n    subparsers.add_parser("status")',
    '    subparsers.add_parser("graduate-lab-doctor")\n'
    '    fixed_doctor = subparsers.add_parser("enable-fixed-doctor")\n'
    '    fixed_doctor.add_argument("--agent-uid", required=True, type=int)\n'
    '    subparsers.add_parser("disable-fixed-doctor")\n'
    '    subparsers.add_parser("status")',
)
fixed_admin = '''        elif args.command == "enable-fixed-doctor":
            agent = store.connection.execute(
                "SELECT unix_uid,state FROM agents WHERE agent_id='agent-aster-fixed-doctor'"
            ).fetchone()
            if agent is not None and tuple(agent) != (args.agent_uid, "observer"):
                raise SystemExit("existing fixed Doctor agent does not match the dedicated observer")
            other_grants = store.connection.execute(
                "SELECT capability FROM agent_capabilities WHERE agent_id='agent-aster-fixed-doctor' "
                "AND capability!='diagnostic.aster-inference.latest'"
            ).fetchall()
            if other_grants:
                raise SystemExit("fixed Doctor agent has another capability grant")
            service = store.connection.execute(
                """SELECT execution_mode,credential_type,custody_identifier,credential_scope,
                          rotation_due,revocation_method FROM services
                     WHERE service_id='aster-fixed-doctor'"""
            ).fetchone()
            expected_service = (
                "proxy", "none", "none", "fixed aster.agent_inference read only",
                "not-applicable", "disable service and stop dedicated caller",
            )
            if service is not None and tuple(service) != expected_service:
                raise SystemExit("existing fixed Doctor service metadata conflicts")
            capability = store.connection.execute(
                "SELECT service_id,risk_class,probation_allowed FROM capabilities "
                "WHERE capability='diagnostic.aster-inference.latest'"
            ).fetchone()
            if capability is not None and tuple(capability) != ("aster-fixed-doctor", "green", 0):
                raise SystemExit("existing fixed Doctor capability metadata conflicts")
            if agent is None:
                store.register_agent("agent-aster-fixed-doctor", args.agent_uid)
                store.set_agent_state("agent-aster-fixed-doctor", "observer")
            with store.connection:
                store.connection.execute(
                    """INSERT OR IGNORE INTO services(
                           service_id,execution_mode,enabled,created_at,credential_type,
                           custody_identifier,credential_scope,rotation_due,revocation_method,health
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    ("aster-fixed-doctor", *expected_service[:1], 1, store._now(),
                     *expected_service[1:], "candidate"),
                )
                store.connection.execute(
                    "UPDATE services SET enabled=1 WHERE service_id='aster-fixed-doctor'"
                )
                store.connection.execute(
                    """INSERT OR IGNORE INTO capabilities(
                           capability,service_id,risk_class,probation_allowed,enabled
                       ) VALUES('diagnostic.aster-inference.latest','aster-fixed-doctor','green',0,1)"""
                )
                store.connection.execute(
                    "UPDATE capabilities SET enabled=1 WHERE capability='diagnostic.aster-inference.latest'"
                )
                store.connection.execute(
                    """INSERT OR IGNORE INTO agent_capabilities(agent_id,capability)
                       VALUES('agent-aster-fixed-doctor','diagnostic.aster-inference.latest')"""
                )
            print("FIXED_DOCTOR_ENABLED agent=agent-aster-fixed-doctor state=observer risk=green")
        elif args.command == "disable-fixed-doctor":
            store.set_service_enabled("aster-fixed-doctor", False)
            grant = store.connection.execute(
                """SELECT 1 FROM agent_capabilities
                     WHERE agent_id='agent-aster-fixed-doctor'
                       AND capability='diagnostic.aster-inference.latest'"""
            ).fetchone()
            if grant is not None:
                store.revoke_capability(
                    "agent-aster-fixed-doctor", "diagnostic.aster-inference.latest",
                )
            store.set_agent_state("agent-aster-fixed-doctor", "suspended")
            print("FIXED_DOCTOR_DISABLED")
'''
text = replace_once(
    text,
    '        else:\n            print(json.dumps({"global_enabled": store.global_enabled(), "audit_events": len(store.audit_rows())}, sort_keys=True))',
    fixed_admin + '        else:\n            print(json.dumps({"global_enabled": store.global_enabled(), "audit_events": len(store.audit_rows())}, sort_keys=True))',
)
admin.write_text(text)

text = service.read_text()
text = replace_once(
    text,
    '            record = self.server.store.consume_request(str(request.get("request_id", "")), payload, agent_id=agent_id)  # type: ignore[attr-defined]',
    '            request_id = str(request.get("request_id", ""))\n'
    '            pending = self.server.store.get_request(request_id)  # type: ignore[attr-defined]\n'
    '            if pending.capability == "diagnostic.aster-inference.latest" and payload != {}:\n'
    '                raise BrokerDenied("fixed Doctor capability accepts no arguments")\n'
    '            record = self.server.store.consume_request(request_id, payload, agent_id=agent_id)  # type: ignore[attr-defined]',
)
fixed_service = '''            if record.capability == "diagnostic.aster-inference.latest":
                rpc = {
                    "method": "doctor.aster-inference.latest",
                    "request_id": record.request_id,
                    "arguments": {},
                }
                try:
                    with socket.socket(socket.AF_UNIX) as gateway:
                        gateway.settimeout(5)
                        gateway.connect(self.server.fixed_doctor_socket)  # type: ignore[attr-defined]
                        gateway.sendall(json.dumps(rpc, separators=(",", ":")).encode() + b"\\n")
                        result = json.loads(gateway.makefile("rb").readline())
                except (OSError, json.JSONDecodeError) as error:
                    raise BrokerDenied("Fixed Doctor gateway is unavailable") from error
                if not isinstance(result, dict) or set(result) != {"ok", "result"} or result.get("ok") is not True:
                    raise BrokerDenied("Fixed Doctor gateway denied the request")
                return {"request_id": record.request_id, "status": record.status, "result": result["result"]}
'''
text = replace_once(
    text,
    '            return {"request_id": record.request_id, "status": record.status, "synthetic": True}',
    fixed_service + '            return {"request_id": record.request_id, "status": record.status, "synthetic": True}',
)
text = replace_once(
    text,
    '        forgejo_project_write_socket: str = "/run/homelab-forgejo-mcp-project-write/gateway.sock",\n        request_timeout: float = 5.0,',
    '        forgejo_project_write_socket: str = "/run/homelab-forgejo-mcp-project-write/gateway.sock",\n'
    '        fixed_doctor_socket: str = "/run/aster-fixed-doctor/gateway.sock",\n'
    '        request_timeout: float = 5.0,',
)
text = replace_once(
    text,
    '        self.lab_operations_socket = lab_operations_socket\n        self.request_timeout = request_timeout',
    '        self.lab_operations_socket = lab_operations_socket\n'
    '        self.fixed_doctor_socket = fixed_doctor_socket\n'
    '        self.request_timeout = request_timeout',
)
text = replace_once(
    text,
    '    parser.add_argument("--lab-operations-socket", default="/run/aster-lab-operations-broker/gateway.sock")\n    args = parser.parse_args()',
    '    parser.add_argument("--lab-operations-socket", default="/run/aster-lab-operations-broker/gateway.sock")\n'
    '    parser.add_argument("--fixed-doctor-socket", default="/run/aster-fixed-doctor/gateway.sock")\n'
    '    args = parser.parse_args()',
)
text = replace_once(
    text,
    '    server = BrokerServer(\n        str(socket_path), store, args.forgejo_socket, args.forgejo_write_socket,\n        args.lab_operations_socket, args.forgejo_project_write_socket,\n    )',
    '    server = BrokerServer(\n'
    '        str(socket_path), store,\n'
    '        forgejo_socket=args.forgejo_socket,\n'
    '        forgejo_write_socket=args.forgejo_write_socket,\n'
    '        lab_operations_socket=args.lab_operations_socket,\n'
    '        forgejo_project_write_socket=args.forgejo_project_write_socket,\n'
    '        fixed_doctor_socket=args.fixed_doctor_socket,\n'
    '    )',
)
service.write_text(text)


results = {}
for name, path in {"broker_admin.py": admin, "broker_service.py": service}.items():
    actual = digest(path)
    if actual != CANDIDATES[name]:
        raise SystemExit(f"{name}: candidate drift: {actual}")
    results[name] = {"predecessor_sha256": PREDECESSORS[name], "candidate_sha256": actual}
print(json.dumps(results, sort_keys=True))
