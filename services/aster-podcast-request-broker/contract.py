"""Strict semantic types for the Aster podcast request queue."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from urllib.parse import SplitResult, urlsplit, urlunsplit


PROVIDER_ID = re.compile(r"[1-9][0-9]{0,31}")
COUNTRY = re.compile(r"[a-z]{2}")
IDEMPOTENCY = re.compile(r"[A-Za-z0-9_-]{24,96}")
OPAQUE_REF = re.compile(r"(?:cand|req)_[A-Za-z0-9_-]{24,96}")


class ContractError(ValueError):
    """The request is outside the podcast queue contract."""


def bounded_text(value: object, *, field: str, maximum: int, minimum: int = 1) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{field}-type")
    text = " ".join(value.split())
    if not minimum <= len(text) <= maximum or any(ord(char) < 32 for char in text):
        raise ContractError(f"{field}-bounds")
    return text


def canonical_https_url(value: object, *, field: str, maximum: int = 2048) -> str:
    raw = bounded_text(value, field=field, maximum=maximum)
    try:
        parsed = urlsplit(raw)
        port = parsed.port
        host = (parsed.hostname or "").encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError) as error:
        raise ContractError(f"{field}-url") from error
    if (parsed.scheme.lower() != "https" or not host or parsed.username is not None
            or parsed.password is not None or port not in {None, 443}
            or not parsed.path.startswith("/") or parsed.fragment):
        raise ContractError(f"{field}-url")
    netloc = host + (f":{port}" if port is not None else "")
    return urlunsplit(SplitResult("https", netloc, parsed.path, parsed.query, ""))


def feed_sha256(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


@dataclass(frozen=True)
class Identity:
    client_id: str
    profile_id: str

    def __post_init__(self) -> None:
        bounded_text(self.client_id, field="client-id", maximum=64)
        bounded_text(self.profile_id, field="profile-id", maximum=64)


@dataclass(frozen=True)
class Candidate:
    provider_id: str
    feed_url: str
    title: str
    artist: str
    artwork_url: str | None

    @classmethod
    def parse(cls, value: object) -> "Candidate":
        if not isinstance(value, dict) or set(value) != {
            "provider_id", "feed_url", "title", "artist", "artwork_url"
        }:
            raise ContractError("candidate-schema")
        provider_id = str(value["provider_id"])
        if not PROVIDER_ID.fullmatch(provider_id):
            raise ContractError("provider-id")
        artwork = value["artwork_url"]
        if artwork is not None:
            artwork = canonical_https_url(artwork, field="artwork-url")
        return cls(
            provider_id=provider_id,
            feed_url=canonical_https_url(value["feed_url"], field="feed-url"),
            title=bounded_text(value["title"], field="title", maximum=240),
            artist=bounded_text(value["artist"], field="artist", maximum=240),
            artwork_url=artwork,
        )


def parse_search(value: object) -> tuple[str, str]:
    if not isinstance(value, dict) or set(value) != {"term", "country"}:
        raise ContractError("search-schema")
    term = bounded_text(value["term"], field="term", minimum=2, maximum=120)
    country = bounded_text(value["country"], field="country", minimum=2, maximum=2).lower()
    if not COUNTRY.fullmatch(country):
        raise ContractError("country")
    return term, country


def parse_request(value: object) -> tuple[str, str]:
    if not isinstance(value, dict) or set(value) != {"candidate_ref", "idempotency_key", "confirm"}:
        raise ContractError("request-schema")
    candidate_ref = value["candidate_ref"]
    key = value["idempotency_key"]
    if not isinstance(candidate_ref, str) or not OPAQUE_REF.fullmatch(candidate_ref):
        raise ContractError("candidate-ref")
    if not isinstance(key, str) or not IDEMPOTENCY.fullmatch(key):
        raise ContractError("idempotency-key")
    if value["confirm"] is not True:
        raise ContractError("explicit-confirmation-required")
    return candidate_ref, key
