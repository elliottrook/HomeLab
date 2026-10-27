"""Fail-closed Music/Books request contract for AsterTV discovery items.

This module performs no I/O.  A broker must read the authoritative discovery
feed, resolve the exact candidate here, then perform provider revalidation
before calling Lidarr or LazyLibrarian.
"""

from dataclasses import dataclass
import re
from typing import Any, Mapping


MBID = re.compile(
    r"musicbrainz:release-group:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12})", re.IGNORECASE)
OPENLIBRARY = re.compile(
    r"openlibrary:(/(?:works/OL[1-9][0-9]{0,12}W|"
    r"books/OL[1-9][0-9]{0,12}M))")
TYPES = {"album": ("music", "musicbrainz"),
         "ebook": ("books", "openlibrary"),
         "audiobook": ("books", "openlibrary")}


class ContractError(ValueError):
    pass


def require(value, code):
    if not value:
        raise ContractError(code)


@dataclass(frozen=True)
class Command:
    identity: str
    media_type: str
    domain: str
    authority: str
    authority_id: str
    title: str


def proposal(value: Any) -> dict[str, Any]:
    require(type(value) is dict
            and set(value) == {"schema", "candidate_id", "media_type",
                               "confirm"}
            and value.get("schema") == 1 and value.get("confirm") is True
            and value.get("media_type") in TYPES
            and isinstance(value.get("candidate_id"), str),
            "acquisition-proposal-invalid")
    media_type = value["media_type"]
    identity = value["candidate_id"]
    match = MBID.fullmatch(identity) if media_type == "album" else OPENLIBRARY.fullmatch(identity)
    require(match is not None, "acquisition-proposal-identity")
    return dict(value)


def resolve(feed: Mapping[str, Any], value: Any) -> Command:
    accepted = proposal(value)
    require(isinstance(feed, Mapping)
            and set(feed) == {"schema", "generated_at", "items"}
            and feed.get("schema") == 1 and isinstance(feed.get("items"), list)
            and len(feed["items"]) <= 12,
            "acquisition-feed-invalid")
    identity = accepted["candidate_id"]
    matches = [item for item in feed["items"]
               if isinstance(item, Mapping) and item.get("identity") == identity]
    require(len(matches) == 1, "acquisition-candidate-unavailable")
    item = matches[0]
    media_type = accepted["media_type"]
    domain, authority = TYPES[media_type]
    require(item.get("media_type") == media_type
            and isinstance(item.get("title"), str)
            and 1 <= len(item["title"].strip()) <= 200
            and item.get("owned") is False and item.get("archived") is False
            and item.get("request_state") == "none"
            and item.get("primary_action") == "request",
            "acquisition-candidate-changed")
    match = MBID.fullmatch(identity) if authority == "musicbrainz" else OPENLIBRARY.fullmatch(identity)
    require(match is not None, "acquisition-candidate-changed")
    return Command(identity, media_type, domain, authority,
                   match.group(1).lower() if authority == "musicbrainz"
                   else match.group(1), item["title"].strip())


def response(command: Command, status: str, request_id: Any) -> dict[str, Any]:
    require(isinstance(command, Command)
            and status in ("pending", "processing", "available"),
            "acquisition-response-invalid")
    require((status == "available" and request_id is None)
            or (status != "available" and type(request_id) in (str, int)
                and type(request_id) is not bool
                and 1 <= len(str(request_id)) <= 80),
            "acquisition-response-invalid")
    return {"schema": 1, "identity": command.identity,
            "status": status, "request_id": request_id}

