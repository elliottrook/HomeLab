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
        else:
            print(json.dumps({"global_enabled": store.global_enabled(), "audit_events": len(store.audit_rows())}, sort_keys=True))
    finally:
        store.close()


if __name__ == "__main__":
    main()
