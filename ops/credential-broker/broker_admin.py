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
    project_documents = subparsers.add_parser("enable-forgejo-project-documents")
    project_documents.add_argument("--agent-id", default="agent-cloud-bundle")
    bundle_runner = subparsers.add_parser("enable-forgejo-bundle-runner")
    bundle_runner.add_argument("--agent-uid", required=True, type=int)
    subparsers.add_parser("enable-forgejo-bundle-read")
    subparsers.add_parser("enable-lab-doctor")
    subparsers.add_parser("disable-lab-doctor")
    subparsers.add_parser("graduate-lab-doctor")
    fixed_doctor = subparsers.add_parser("enable-fixed-doctor")
    fixed_doctor.add_argument("--agent-uid", required=True, type=int)
    subparsers.add_parser("disable-fixed-doctor")
    fixed_speech = subparsers.add_parser("enable-fixed-speech")
    fixed_speech.add_argument("--agent-uid", required=True, type=int)
    subparsers.add_parser("disable-fixed-speech")
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
        elif args.command == "enable-forgejo-project-documents":
            agent = store.connection.execute(
                "SELECT state FROM agents WHERE agent_id=?", (args.agent_id,)
            ).fetchone()
            if agent is None or agent[0] not in {"operator", "specialist", "orchestrator"}:
                raise SystemExit("project-document agent must already be promoted")
            with store.connection:
                store.connection.execute(
                    """INSERT OR IGNORE INTO services(
                           service_id,execution_mode,enabled,created_at,credential_type,
                           custody_identifier,credential_scope,rotation_due,revocation_method,health
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "forgejo-mcp-project-write", "proxy", 1, store._now(), "Forgejo PAT",
                        "secret/ai-pam/forgejo-mcp-project-write",
                        "jason/homelab docs/projects and docs/handovers create only",
                        "operator-managed", "disable service and revoke PAT", "candidate",
                    ),
                )
                store.connection.execute(
                    """INSERT OR IGNORE INTO capabilities(
                           capability,service_id,risk_class,probation_allowed,enabled
                       ) VALUES('forgejo.write.project-documents','forgejo-mcp-project-write','yellow',0,1)"""
                )
                store.connection.execute(
                    "INSERT OR IGNORE INTO agent_capabilities(agent_id,capability) VALUES(?,?)",
                    (args.agent_id, "forgejo.write.project-documents"),
                )
            print("FORGEJO_PROJECT_DOCUMENTS_ENABLED")
        elif args.command == "enable-forgejo-bundle-runner":
            capability = store.connection.execute(
                "SELECT risk_class,probation_allowed,enabled FROM capabilities "
                "WHERE capability='forgejo.write.safe-branch'"
            ).fetchone()
            if capability is None or tuple(capability) != ("yellow", 0, 1):
                raise SystemExit("existing Forgejo safe-write capability is not ready")
            existing = store.connection.execute(
                "SELECT unix_uid,state FROM agents WHERE agent_id='agent-cloud-bundle'"
            ).fetchone()
            if existing is None:
                store.register_agent("agent-cloud-bundle", args.agent_uid)
            elif tuple(existing) != (args.agent_uid, "probation"):
                raise SystemExit("existing bundle-runner identity does not match probation policy")
            with store.connection:
                store.connection.execute(
                    "INSERT OR IGNORE INTO agent_capabilities(agent_id,capability) "
                    "VALUES('agent-cloud-bundle','forgejo.write.safe-branch')"
                )
            print("FORGEJO_BUNDLE_RUNNER_ENABLED state=probation")
        elif args.command == "enable-forgejo-bundle-read":
            capability = store.connection.execute(
                "SELECT service_id,risk_class,probation_allowed,enabled FROM capabilities "
                "WHERE capability='forgejo.read.repository'"
            ).fetchone()
            if capability is None or tuple(capability) != ("forgejo-mcp", "green", 0, 1):
                raise SystemExit("existing Forgejo read capability is not ready")
            agent = store.connection.execute(
                "SELECT state FROM agents WHERE agent_id='agent-cloud-bundle'"
            ).fetchone()
            if agent is None or agent[0] not in {"operator", "specialist", "orchestrator"}:
                raise SystemExit("bundle-runner identity is not an active promoted agent")
            with store.connection:
                store.connection.execute(
                    "INSERT OR IGNORE INTO agent_capabilities(agent_id,capability) "
                    "VALUES('agent-cloud-bundle','forgejo.read.repository')"
                )
            print("FORGEJO_BUNDLE_READ_ENABLED risk=green repository=jason/homelab")
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
        elif args.command == "graduate-lab-doctor":
            service = store.connection.execute(
                "SELECT enabled FROM services WHERE service_id='lab-operations'"
            ).fetchone()
            capabilities = store.connection.execute(
                """SELECT capability,risk_class,enabled FROM capabilities
                     WHERE service_id='lab-operations' ORDER BY capability"""
            ).fetchall()
            grants = store.connection.execute(
                """SELECT capability FROM agent_capabilities
                     WHERE agent_id='agent-hermes' AND capability LIKE 'lab.doctor.%'
                     ORDER BY capability"""
            ).fetchall()
            active = store.connection.execute(
                """SELECT count(*) FROM requests WHERE capability LIKE 'lab.doctor.%'
                     AND status IN ('pending','approved')"""
            ).fetchone()[0]
            expected_capabilities = [
                ("lab.doctor.latest", "green", 1),
                ("lab.doctor.run", "yellow", 1),
            ]
            expected_grants = [("lab.doctor.latest",), ("lab.doctor.run",)]
            if service is None or tuple(service) != (1,) or [tuple(row) for row in capabilities] != expected_capabilities:
                raise SystemExit("lab-operations service is not in its enabled M7 shape")
            if [tuple(row) for row in grants] != expected_grants or active:
                raise SystemExit("lab-operations grants or requests are not ready for graduation")
            with store.connection:
                store.connection.execute(
                    "UPDATE services SET health='healthy' WHERE service_id='lab-operations'"
                )
            print("LAB_DOCTOR_GRADUATED")
        elif args.command == "enable-fixed-doctor":
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
        elif args.command == "enable-fixed-speech":
            agent = store.connection.execute(
                "SELECT unix_uid,state FROM agents WHERE agent_id='agent-aster-fixed-speech'"
            ).fetchone()
            if agent is not None and tuple(agent) != (args.agent_uid, "observer"):
                raise SystemExit("existing fixed Speech agent does not match the dedicated observer")
            other_grants = store.connection.execute(
                "SELECT capability FROM agent_capabilities WHERE agent_id='agent-aster-fixed-speech' "
                "AND capability!='diagnostic.aster-speech.latest'"
            ).fetchall()
            if other_grants:
                raise SystemExit("fixed Speech agent has another capability grant")
            service = store.connection.execute(
                """SELECT execution_mode,credential_type,custody_identifier,credential_scope,
                          rotation_due,revocation_method FROM services
                     WHERE service_id='aster-fixed-speech'"""
            ).fetchone()
            expected_service = (
                "proxy", "none", "none", "fixed aster.speech read only",
                "not-applicable", "disable service and stop dedicated caller",
            )
            if service is not None and tuple(service) != expected_service:
                raise SystemExit("existing fixed Speech service metadata conflicts")
            capability = store.connection.execute(
                "SELECT service_id,risk_class,probation_allowed FROM capabilities "
                "WHERE capability='diagnostic.aster-speech.latest'"
            ).fetchone()
            if capability is not None and tuple(capability) != ("aster-fixed-speech", "green", 0):
                raise SystemExit("existing fixed Speech capability metadata conflicts")
            if agent is None:
                store.register_agent("agent-aster-fixed-speech", args.agent_uid)
                store.set_agent_state("agent-aster-fixed-speech", "observer")
            with store.connection:
                store.connection.execute(
                    """INSERT OR IGNORE INTO services(
                           service_id,execution_mode,enabled,created_at,credential_type,
                           custody_identifier,credential_scope,rotation_due,revocation_method,health
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    ("aster-fixed-speech", *expected_service[:1], 1, store._now(),
                     *expected_service[1:], "candidate"),
                )
                store.connection.execute(
                    "UPDATE services SET enabled=1 WHERE service_id='aster-fixed-speech'"
                )
                store.connection.execute(
                    """INSERT OR IGNORE INTO capabilities(
                           capability,service_id,risk_class,probation_allowed,enabled
                       ) VALUES('diagnostic.aster-speech.latest','aster-fixed-speech','green',0,1)"""
                )
                store.connection.execute(
                    "UPDATE capabilities SET enabled=1 WHERE capability='diagnostic.aster-speech.latest'"
                )
                store.connection.execute(
                    """INSERT OR IGNORE INTO agent_capabilities(agent_id,capability)
                       VALUES('agent-aster-fixed-speech','diagnostic.aster-speech.latest')"""
                )
            print("FIXED_SPEECH_ENABLED agent=agent-aster-fixed-speech state=observer risk=green")
        elif args.command == "disable-fixed-speech":
            store.set_service_enabled("aster-fixed-speech", False)
            grant = store.connection.execute(
                """SELECT 1 FROM agent_capabilities
                     WHERE agent_id='agent-aster-fixed-speech'
                       AND capability='diagnostic.aster-speech.latest'"""
            ).fetchone()
            if grant is not None:
                store.revoke_capability(
                    "agent-aster-fixed-speech", "diagnostic.aster-speech.latest",
                )
            store.set_agent_state("agent-aster-fixed-speech", "suspended")
            print("FIXED_SPEECH_DISABLED")
        else:
            print(json.dumps({"global_enabled": store.global_enabled(), "audit_events": len(store.audit_rows())}, sort_keys=True))
    finally:
        store.close()


if __name__ == "__main__":
    main()
