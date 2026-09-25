"""Disposable, offline review probes. No production connection or credential."""
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent / "source-snapshot/ops/credential-broker"))
from broker_core import BrokerStore
from broker_service import BrokerHandler

results = []
with tempfile.TemporaryDirectory() as tmp:
    store = BrokerStore(Path(tmp) / "test.db", clock=lambda: 1000)
    store.register_agent("synthetic-a", 12345)
    store.register_agent("synthetic-b", 12346)
    store.register_service("synthetic")
    store.register_capability("synthetic.read", "synthetic", "green", probation_allowed=True)
    store.register_capability("synthetic.change", "synthetic", "yellow")
    store.grant_capability("synthetic-a", "synthetic.read")
    store.grant_capability("synthetic-a", "synthetic.change")
    request = store.create_request("synthetic-a", "synthetic.read", {"fixture": 1})
    handler = object.__new__(BrokerHandler)
    handler.server = SimpleNamespace(store=store)
    result = handler.dispatch("synthetic-b", {"method": "request.consume", "request_id": request.request_id, "payload": {"fixture": 1}})
    results.append({"probe": "different_registered_caller_consumes_request", "observed": result["status"], "synthetic_only": result["synthetic"]})
    store.set_agent_state("synthetic-a", "operator")
    request = store.create_request("synthetic-a", "synthetic.change", {"fixture": 2})
    store.approve_request(request.request_id, request.payload_hash)
    store.set_agent_state("synthetic-a", "probation")
    result = handler.dispatch("synthetic-a", {"method": "request.consume", "request_id": request.request_id, "payload": {"fixture": 2}})
    results.append({"probe": "approved_yellow_survives_demotion_to_probation", "observed": result["status"], "synthetic_only": result["synthetic"]})
    store.close()
text = json.dumps({"source_commit": "e50b670b906f397e1e70b6d51cf07e88235ac5c5", "results": results, "limit": "Offline source-path probes; no production exploit or production action attempted."}, indent=2)
(Path(__file__).parent / "broker-probe-results.json").write_text(text + "\n")
print(text)
