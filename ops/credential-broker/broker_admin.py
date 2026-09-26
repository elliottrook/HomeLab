#!/usr/bin/env python3
"""Root/operator administration for the M2 synthetic broker state."""

from __future__ import annotations

import argparse
import json

from broker_core import BrokerStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    initialize = subparsers.add_parser("initialize-synthetic")
    initialize.add_argument("--agent-uid", required=True, type=int)
    subparsers.add_parser("global-disable")
    subparsers.add_parser("global-enable")
    subparsers.add_parser("enable-forgejo-safe-write")
    subparsers.add_parser("enable-lab-doctor")
    subparsers.add_parser("disable-lab-doctor")
    subparsers.add_parser("status")
    args = parser.parse_args()
    store = BrokerStore(args.database)
    try:
        if args.command == "initialize-synthetic":
            store.register_agent("agent-hermes", args.agent_uid)
            store.register_service("synthetic", "proxy")
            store.register_capability("broker.health.read", "synthetic", "green", probation_allowed=True)
            store.register_capability("broker.synthetic.restart", "synthetic", "yellow")
            store.register_capability("broker.synthetic.network-change", "synthetic", "red")
            store.register_capability("broker.root-material", "synthetic", "black")
            for capability in (
                "broker.health.read", "broker.synthetic.restart",
                "broker.synthetic.network-change", "broker.root-material",
            ):
                store.grant_capability("agent-hermes", capability)
            print("INITIALIZED agent=agent-hermes state=probation service=synthetic")
        elif args.command == "global-disable":
            store.set_global_enabled(False)
            print("GLOBAL_DISABLED")
        elif args.command == "global-enable":
            store.set_global_enabled(True)
            print("GLOBAL_ENABLED")
        elif args.command == "enable-forgejo-safe-write":
            if store.connection.execute(
                "SELECT 1 FROM agents WHERE agent_id='agent-hermes'"
            ).fetchone() is None:
                raise SystemExit("agent-hermes is not registered")
            with store.connection:
                store.connection.execute(
                    """INSERT OR IGNORE INTO services(
                           service_id,execution_mode,enabled,created_at,credential_type,
                           custody_identifier,credential_scope,rotation_due,revocation_method,health
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "forgejo-mcp-safe-write", "proxy", 1, store._now(), "Forgejo PAT",
                        "secret/ai-pam/forgejo-mcp-safe-write", "jason/homelab safe-branch create only",
                        "operator-managed", "disable service and revoke PAT", "candidate",
                    ),
                )
                store.connection.execute(
                    """INSERT OR IGNORE INTO capabilities(
                           capability,service_id,risk_class,probation_allowed,enabled
                       ) VALUES('forgejo.write.safe-branch','forgejo-mcp-safe-write','yellow',0,1)"""
                )
                store.connection.execute(
                    """INSERT OR IGNORE INTO agent_capabilities(agent_id,capability)
                       VALUES('agent-hermes','forgejo.write.safe-branch')"""
                )
            print("FORGEJO_SAFE_WRITE_ENABLED")
        elif args.command == "enable-lab-doctor":
            if store.connection.execute(
                "SELECT 1 FROM agents WHERE agent_id='agent-hermes'"
            ).fetchone() is None:
                raise SystemExit("agent-hermes is not registered")
            with store.connection:
                store.connection.execute(
                    """INSERT OR IGNORE INTO services(
                           service_id,execution_mode,enabled,created_at,credential_type,
                           custody_identifier,credential_scope,rotation_due,revocation_method,health
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "lab-operations", "proxy", 1, store._now(), "none", "none",
                        "doctor diagnostics only", "not-applicable",
                        "disable lab-operations broker service", "candidate",
                    ),
                )
                store.connection.execute(
                    "UPDATE services SET enabled=1 WHERE service_id='lab-operations'"
                )
                service = store.connection.execute(
                    """SELECT execution_mode,credential_type,custody_identifier,credential_scope,
                              rotation_due,revocation_method
                         FROM services WHERE service_id='lab-operations'"""
                ).fetchone()
                if tuple(service) != (
                    "proxy", "none", "none", "doctor diagnostics only", "not-applicable",
                    "disable lab-operations broker service",
                ):
                    raise SystemExit("existing lab-operations service metadata does not match M7")
                for capability, risk, probation in (
                    ("lab.doctor.latest", "green", 1),
                    ("lab.doctor.run", "yellow", 0),
                ):
                    store.connection.execute(
                        """INSERT OR IGNORE INTO capabilities(
                               capability,service_id,risk_class,probation_allowed,enabled
                           ) VALUES(?,?,?,?,1)""",
                        (capability, "lab-operations", risk, probation),
                    )
                    store.connection.execute(
                        "UPDATE capabilities SET enabled=1 WHERE capability=?", (capability,),
                    )
                    registered = store.connection.execute(
                        """SELECT service_id,risk_class,probation_allowed
                             FROM capabilities WHERE capability=?""", (capability,),
                    ).fetchone()
                    if tuple(registered) != ("lab-operations", risk, probation):
                        raise SystemExit(f"existing {capability} metadata does not match M7")
                    store.connection.execute(
                        """INSERT OR IGNORE INTO agent_capabilities(agent_id,capability)
                           VALUES('agent-hermes',?)""",
                        (capability,),
                    )
            print("LAB_DOCTOR_ENABLED")
        elif args.command == "disable-lab-doctor":
            store.set_service_enabled("lab-operations", False)
            print("LAB_DOCTOR_DISABLED")
        else:
            print(json.dumps({"global_enabled": store.global_enabled(), "audit_events": len(store.audit_rows())}, sort_keys=True))
    finally:
        store.close()


if __name__ == "__main__":
    main()
