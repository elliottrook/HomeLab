"""Semantic podcast discovery and owner-approved queue core."""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Callable, Protocol

from contract import (Candidate, ContractError, Identity, OPAQUE_REF, feed_sha256,
                      parse_request, parse_search)
from persistence import QueueStore


CANDIDATE_TTL = 15 * 60
MAX_RESULTS = 20


class Catalogue(Protocol):
    def search(self, term: str, country: str) -> list[dict]: ...
    def identities(self) -> tuple[set[str], set[str]]: ...


class BrokerError(RuntimeError):
    pass


def _opaque(prefix: str, factory: Callable[[int], str]) -> str:
    value = f"{prefix}_{factory(32)}"
    if not OPAQUE_REF.fullmatch(value):
        raise BrokerError("opaque-reference")
    return value


def _public_candidate(reference: str, record: dict) -> dict:
    return {
        "candidate_ref": reference,
        "title": record["title"],
        "artist": record["artist"],
        "artwork_url": record["artwork_url"],
        "status": record["status"],
        "expires_at": record["expires_at"],
    }


class PodcastRequestBroker:
    def __init__(self, store: QueueStore, catalogue: Catalogue, *,
                 now: Callable[[], int] = lambda: int(time.time()),
                 token_factory: Callable[[int], str] = secrets.token_urlsafe):
        self.store = store
        self.catalogue = catalogue
        self.now = now
        self.token_factory = token_factory

    def search(self, identity: Identity, body: object) -> dict:
        term, country = parse_search(body)
        current = self.now()
        feed_ids, provider_ids = self.catalogue.identities()
        parsed: list[Candidate] = []
        seen: set[tuple[str, str]] = set()
        for raw in self.catalogue.search(term, country)[:MAX_RESULTS]:
            try:
                candidate = Candidate.parse(raw)
            except ContractError:
                # External catalogue records are untrusted individually. An
                # unsafe feed or artwork URL must disappear, not make every
                # otherwise valid result unavailable.
                continue
            key = (candidate.provider_id, feed_sha256(candidate.feed_url))
            if key not in seen:
                seen.add(key)
                parsed.append(candidate)

        def save(state: dict) -> dict:
            state["candidates"] = {
                key: value for key, value in state["candidates"].items()
                if value.get("expires_at", 0) >= current
            }
            output = []
            for candidate in parsed:
                reference = _opaque("cand", self.token_factory)
                feed_hash = feed_sha256(candidate.feed_url)
                status = ("already_subscribed" if candidate.provider_id in provider_ids
                          or feed_hash in feed_ids else "available_to_request")
                record = {
                    "client_id": identity.client_id, "profile_id": identity.profile_id,
                    "provider_id": candidate.provider_id, "feed_url": candidate.feed_url,
                    "feed_sha256": feed_hash, "title": candidate.title,
                    "artist": candidate.artist, "artwork_url": candidate.artwork_url,
                    "status": status, "expires_at": current + CANDIDATE_TTL,
                }
                state["candidates"][reference] = record
                output.append(_public_candidate(reference, record))
            return {"results": output, "count": len(output)}

        return self.store.transact(save, write=True)

    def request(self, identity: Identity, body: object) -> dict:
        candidate_ref, idempotency_key = parse_request(body)
        current = self.now()
        scoped_key = hashlib.sha256(
            f"{identity.client_id}\0{identity.profile_id}\0{idempotency_key}".encode()
        ).hexdigest()

        def enqueue(state: dict) -> dict:
            prior_ref = state["idempotency"].get(scoped_key)
            if prior_ref:
                prior = state["requests"].get(prior_ref)
                if prior is None or prior.get("candidate_ref") != candidate_ref:
                    raise ContractError("idempotency-conflict")
                return self._public_request(prior_ref, prior, duplicate=True)
            candidate = state["candidates"].get(candidate_ref)
            if candidate is None or candidate.get("expires_at", 0) < current:
                raise ContractError("candidate-stale")
            if (candidate.get("client_id") != identity.client_id
                    or candidate.get("profile_id") != identity.profile_id):
                raise ContractError("candidate-owner")
            if candidate.get("status") != "available_to_request":
                raise ContractError("already-subscribed")
            for reference, request in state["requests"].items():
                if (request.get("provider_id") == candidate["provider_id"]
                        or request.get("feed_sha256") == candidate["feed_sha256"]):
                    state["idempotency"][scoped_key] = reference
                    return self._public_request(reference, request, duplicate=True)
            reference = _opaque("req", self.token_factory)
            record = {
                "candidate_ref": candidate_ref, "client_id": identity.client_id,
                "profile_id": identity.profile_id, "provider_id": candidate["provider_id"],
                "feed_sha256": candidate["feed_sha256"], "title": candidate["title"],
                "artist": candidate["artist"], "artwork_url": candidate["artwork_url"],
                "status": "pending_owner_approval", "created_at": current,
            }
            state["requests"][reference] = record
            state["idempotency"][scoped_key] = reference
            return self._public_request(reference, record, duplicate=False)

        return self.store.transact(enqueue, write=True)

    @staticmethod
    def _public_request(reference: str, record: dict, *, duplicate: bool) -> dict:
        return {
            "request_ref": reference, "status": record["status"],
            "title": record["title"], "artist": record["artist"],
            "artwork_url": record["artwork_url"], "duplicate": duplicate,
            "created_at": record["created_at"],
        }

    def status(self, identity: Identity, request_ref: str) -> dict:
        if not isinstance(request_ref, str) or not OPAQUE_REF.fullmatch(request_ref):
            raise ContractError("request-ref")

        def read(state: dict) -> dict:
            record = state["requests"].get(request_ref)
            if record is None:
                raise ContractError("request-missing")
            if (record.get("client_id") != identity.client_id
                    or record.get("profile_id") != identity.profile_id):
                raise ContractError("request-owner")
            return self._public_request(request_ref, record, duplicate=False)

        return self.store.transact(read, write=False)
