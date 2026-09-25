"""M1 required-denial regressions; expected failures are explicit open blockers.

Synthetic in-memory state only: no sockets, credentials or production actions.
Remove expectedFailure only alongside a verified fix. An unexpected success
fails unittest so a changed baseline cannot silently leave this record stale.
"""

import unittest
from types import SimpleNamespace

from broker_core import BrokerDenied, BrokerStore
from broker_service import BrokerHandler


class AdaptiveFoundationRegressions(unittest.TestCase):
    def setUp(self):
        self.store = BrokerStore(":memory:", clock=lambda: 1000)
        self.addCleanup(self.store.close)
        self.store.register_agent("fixture-owner", 10001)
        self.store.register_agent("fixture-other", 10002)
        self.store.register_service("fixture")
        self.store.register_capability("fixture.read", "fixture", "green", probation_allowed=True)
        self.store.register_capability("fixture.change", "fixture", "yellow")
        for agent in ("fixture-owner", "fixture-other"):
            self.store.grant_capability(agent, "fixture.read")
        self.store.grant_capability("fixture-owner", "fixture.change")
        self.handler = object.__new__(BrokerHandler)
        self.handler.server = SimpleNamespace(store=self.store)

    @unittest.expectedFailure
    def test_consume_must_bind_authenticated_originating_agent(self):
        request = self.store.create_request("fixture-owner", "fixture.read", {})
        with self.assertRaises(BrokerDenied):
            self.handler.dispatch("fixture-other", {
                "method": "request.consume", "request_id": request.request_id, "payload": {},
            })

    @unittest.expectedFailure
    def test_approved_action_must_not_survive_demotion_to_probation(self):
        self.store.set_agent_state("fixture-owner", "operator")
        request = self.store.create_request("fixture-owner", "fixture.change", {})
        self.store.approve_request(request.request_id, request.payload_hash)
        self.store.set_agent_state("fixture-owner", "probation")
        with self.assertRaises(BrokerDenied):
            self.handler.dispatch("fixture-owner", {
                "method": "request.consume", "request_id": request.request_id, "payload": {},
            })


if __name__ == "__main__":
    unittest.main()
