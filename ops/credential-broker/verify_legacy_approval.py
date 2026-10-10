#!/usr/bin/env python3
"""Offline Stage 1 compatibility check; synthetic memory only, no socket/target call.

Load the retained approval service source with the candidate core and transport.
Run this from a staged directory containing this file, broker_core.py and
broker_service.py. The source path must be an operator-selected trusted file.
"""
import argparse
import importlib.util
import json
from types import SimpleNamespace

from broker_core import BrokerDenied, BrokerStore


def verify(path):
    spec = importlib.util.spec_from_file_location("retained_approval_service", path)
    if spec is None or spec.loader is None:
        raise ValueError("approval source is not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    store = BrokerStore(":memory:", clock=lambda: 1000)
    try:
        store.register_agent("fixture", 10001)
        store.set_agent_state("fixture", "operator")
        store.register_service("fixture")
        for name, risk in (("yellow", "yellow"), ("red", "red")):
            store.register_capability(name, "fixture", risk)
            store.grant_capability("fixture", name)
        handler = object.__new__(module.ApprovalHandler)
        handler.server = SimpleNamespace(store=store)
        for capability in ("yellow", "red"):
            request = store.create_request("fixture", capability, {})
            pending = handler.dispatch({"method": "pending.list"})
            if request.request_id not in {item["request_id"] for item in pending}:
                raise AssertionError("retained inbox did not show fixture")
            args = {"method": "request.approve", "request_id": request.request_id,
                    "payload_hash": request.payload_hash, "actor": "a" * 64,
                    "auth_time": 1000, "assurance": "passkey"}
            if capability == "red":
                try:
                    handler.dispatch(args | {"auth_time": 800})
                except BrokerDenied:
                    pass
                else:
                    raise AssertionError("stale red approval accepted")
            handler.dispatch(args)
            try:
                store.consume_request(request.request_id, {}, agent_id="another-fixture")
            except BrokerDenied:
                pass
            else:
                raise AssertionError("wrong caller accepted")
            if store.consume_request(request.request_id, {}, agent_id="fixture").status != "consumed":
                raise AssertionError("valid fixture failed")
            try:
                store.consume_request(request.request_id, {}, agent_id="fixture")
            except BrokerDenied:
                pass
            else:
                raise AssertionError("replay accepted")
    finally:
        store.close()
    return {"legacy_approval_with_candidate_core": "passed", "external_actions": 0,
            "fixtures": ["yellow", "red"], "denials": ["stale-red", "wrong-caller", "replay"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-service", required=True)
    print(json.dumps(verify(parser.parse_args().approval_service), sort_keys=True))
