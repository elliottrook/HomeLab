"""Approval-gated authority adapters for the M2 request portal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from request_contract import Candidate, plan_action

Transport = Callable[[str, str, Optional[Mapping[str, Any]]], Mapping[str, Any]]


@dataclass(frozen=True)
class AdapterResult:
    authority: str
    action: str
    request_id: Optional[str]
    state: str
    response: Mapping[str, Any]


class SeerrAdapter:
    """Seerr movie/TV adapter; authentication is supplied by the transport."""

    authority = "seerr"

    def __init__(self, transport: Transport):
        self._transport = transport

    def request(self, candidate: Candidate, *, media_id: int, approve: bool = False,
                seasons: list[int] | str | None = None) -> AdapterResult:
        plan = plan_action(candidate, approve=approve)
        if not plan["approved"]:
            return AdapterResult(self.authority, "request", None, "blocked", plan)
        if candidate.media_type not in {"movie", "tv"}:
            raise ValueError("Seerr supports only movie or tv candidates")
        body: dict[str, Any] = {"mediaType": candidate.media_type, "mediaId": media_id}
        if seasons is not None:
            body["seasons"] = seasons
        response = self._transport("POST", "/api/v1/request", body)
        return AdapterResult(self.authority, "request", _request_id(response), "submitted", response)


class LidarrAdapter:
    """Narrow album-add adapter; it never accepts an artist-only request."""

    authority = "lidarr"

    def __init__(self, transport: Transport):
        self._transport = transport

    def add_album(self, candidate: Candidate, *, album_id: str, artist_id: str,
                  approve: bool = False) -> AdapterResult:
        plan = plan_action(candidate, approve=approve)
        if not plan["approved"]:
            return AdapterResult(self.authority, "add_album", None, "blocked", plan)
        if candidate.media_type != "album":
            raise ValueError("Lidarr adapter requires an album candidate")
        body = {"albumId": album_id, "artistId": artist_id, "monitored": True,
                "addOptions": {"searchForNewAlbum": True}}
        response = self._transport("POST", "/api/v1/album", body)
        return AdapterResult(self.authority, "add_album", _request_id(response), "submitted", response)


class LazyLibrarianAdapter:
    """Configured wanted-item boundary for ebook/audiobook requests."""

    authority = "lazylibrarian"

    def __init__(self, transport: Transport, wanted_path: str):
        if not wanted_path.startswith("/"):
            raise ValueError("wanted_path must be an absolute API path")
        self._transport = transport
        self._wanted_path = wanted_path

    def add_wanted(self, candidate: Candidate, *, author_id: str,
                   approve: bool = False) -> AdapterResult:
        plan = plan_action(candidate, approve=approve)
        if not plan["approved"]:
            return AdapterResult(self.authority, "add_wanted", None, "blocked", plan)
        if candidate.media_type not in {"ebook", "audiobook"}:
            raise ValueError("LazyLibrarian requires an ebook or audiobook candidate")
        body = {"authorId": author_id, "title": candidate.title, "mediaType": candidate.media_type}
        response = self._transport("POST", self._wanted_path, body)
        return AdapterResult(self.authority, "add_wanted", _request_id(response), "submitted", response)


def _request_id(response: Mapping[str, Any]) -> str | None:
    for key in ("id", "requestId", "albumId", "bookId", "itemId"):
        value = response.get(key)
        if value is not None:
            return str(value)
    return None
