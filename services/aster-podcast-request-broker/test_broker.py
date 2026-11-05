from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from broker import PodcastRequestBroker
from contract import Candidate, ContractError, Identity, canonical_https_url
from persistence import QueueStore


class Catalogue:
    def __init__(self):
        self.existing_feeds: set[str] = set()
        self.existing_ids: set[str] = set()

    def search(self, term, country):
        self.last = (term, country)
        return [{"provider_id": "12345", "feed_url": "https://feeds.example/show.xml",
                 "title": "Synthetic Show", "artist": "Aster Fixtures",
                 "artwork_url": "https://images.example/show.jpg"}]

    def identities(self):
        return self.existing_feeds, self.existing_ids


class Tokens:
    def __init__(self): self.value = 0
    def __call__(self, _size):
        self.value += 1
        return ("A" if self.value % 2 else "B") * 32


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.catalogue = Catalogue()
        self.clock = 1_800_000_000
        self.broker = PodcastRequestBroker(
            QueueStore(Path(self.temp.name)), self.catalogue,
            now=lambda: self.clock, token_factory=Tokens())
        self.jason = Identity("AsterTV-Jen", "jason")

    def search(self):
        return self.broker.search(self.jason, {"term": "synthetic", "country": "ca"})

    def test_search_returns_opaque_candidate_without_feed_or_provider(self):
        result = self.search()
        self.assertEqual(self.catalogue.last, ("synthetic", "ca"))
        self.assertEqual(result["count"], 1)
        item = result["results"][0]
        self.assertEqual(set(item), {"candidate_ref", "title", "artist", "artwork_url",
                                     "status", "expires_at"})
        self.assertNotIn("feed", repr(item).lower())
        self.assertNotIn("12345", repr(item))

    def test_request_is_explicit_and_idempotent(self):
        candidate = self.search()["results"][0]["candidate_ref"]
        body = {"candidate_ref": candidate, "idempotency_key": "x" * 32, "confirm": True}
        first = self.broker.request(self.jason, body)
        second = self.broker.request(self.jason, body)
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["request_ref"], second["request_ref"])
        self.assertEqual(first["status"], "pending_owner_approval")

    def test_same_candidate_with_new_key_deduplicates(self):
        candidate = self.search()["results"][0]["candidate_ref"]
        first = self.broker.request(self.jason, {"candidate_ref": candidate,
            "idempotency_key": "x" * 32, "confirm": True})
        second = self.broker.request(self.jason, {"candidate_ref": candidate,
            "idempotency_key": "y" * 32, "confirm": True})
        self.assertEqual(first["request_ref"], second["request_ref"])
        self.assertTrue(second["duplicate"])

    def test_cross_profile_and_stale_candidates_deny(self):
        candidate = self.search()["results"][0]["candidate_ref"]
        body = {"candidate_ref": candidate, "idempotency_key": "x" * 32, "confirm": True}
        with self.assertRaisesRegex(ContractError, "candidate-owner"):
            self.broker.request(Identity("AsterTV-Jen", "guest"), body)
        self.clock += 901
        with self.assertRaisesRegex(ContractError, "candidate-stale"):
            self.broker.request(self.jason, body)

    def test_subscribed_candidate_cannot_queue(self):
        self.catalogue.existing_ids.add("12345")
        candidate = self.search()["results"][0]
        self.assertEqual(candidate["status"], "already_subscribed")
        with self.assertRaisesRegex(ContractError, "already-subscribed"):
            self.broker.request(self.jason, {"candidate_ref": candidate["candidate_ref"],
                "idempotency_key": "x" * 32, "confirm": True})

    def test_status_is_profile_scoped(self):
        candidate = self.search()["results"][0]["candidate_ref"]
        request = self.broker.request(self.jason, {"candidate_ref": candidate,
            "idempotency_key": "x" * 32, "confirm": True})
        self.assertEqual(self.broker.status(self.jason, request["request_ref"])["status"],
                         "pending_owner_approval")
        with self.assertRaisesRegex(ContractError, "request-owner"):
            self.broker.status(Identity("AsterTV-Jen", "guest"), request["request_ref"])

    def test_contract_rejects_unsafe_feed_and_unconfirmed_request(self):
        with self.assertRaises(ContractError):
            Candidate.parse({"provider_id": "123", "feed_url": "http://127.0.0.1/feed",
                "title": "Bad", "artist": "Bad", "artwork_url": None})
        candidate = self.search()["results"][0]["candidate_ref"]
        with self.assertRaisesRegex(ContractError, "explicit-confirmation"):
            self.broker.request(self.jason, {"candidate_ref": candidate,
                "idempotency_key": "x" * 32, "confirm": False})

    def test_canonical_url_normalizes_host_and_default_port(self):
        self.assertEqual(canonical_https_url("https://EXAMPLE.com:443/feed?q=1", field="feed"),
                         "https://example.com:443/feed?q=1")


if __name__ == "__main__":
    unittest.main()
