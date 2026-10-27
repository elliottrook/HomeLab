"""Credential-free provider adapters for the Aster Acquisition broker.

Each transport is injected after authentication and is expected to be scoped to
one private service. This module never reads or logs a key.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from aster_acquisition_broker import AuthorityResolution, BrokerError
from aster_acquisition_contract import Command


Transport = Callable[[str, str, Optional[Mapping[str, Any]],
                      Optional[Mapping[str, Any]]], tuple[int, Any]]


def require(value, code):
    if not value:
        raise BrokerError(code)


class LidarrProvider:
    def __init__(self, transport: Transport, *, root: str,
                 quality_profile_id: int, metadata_profile_id: int):
        require(callable(transport) and isinstance(root, str) and root.startswith("/")
                and type(quality_profile_id) is int and quality_profile_id > 0
                and type(metadata_profile_id) is int and metadata_profile_id > 0,
                "acquisition-lidarr-configuration")
        self.transport = transport
        self.root = root
        self.quality = quality_profile_id
        self.metadata = metadata_profile_id

    def revalidate(self, command: Command) -> AuthorityResolution:
        require(isinstance(command, Command) and command.media_type == "album"
                and command.authority == "musicbrainz",
                "acquisition-lidarr-command")
        status, existing = self.transport(
            "GET", "/api/v1/album", {"foreignAlbumId": command.authority_id}, None)
        require(status == 200 and isinstance(existing, list),
                "acquisition-lidarr-read")
        exact_existing = [row for row in existing if isinstance(row, Mapping)
                          and row.get("foreignAlbumId") == command.authority_id]
        require(len(exact_existing) <= 1 and len(existing) == len(exact_existing),
                "acquisition-lidarr-existing-ambiguous")
        if exact_existing:
            return AuthorityResolution(command.identity, "available")
        status, lookup = self.transport(
            "GET", "/api/v1/album/lookup", {"term": command.title}, None)
        require(status == 200 and isinstance(lookup, list),
                "acquisition-lidarr-lookup")
        matches = [row for row in lookup if isinstance(row, Mapping)
                   and row.get("foreignAlbumId") == command.authority_id]
        require(len(matches) == 1, "acquisition-lidarr-match")
        return AuthorityResolution(command.identity, "requestable",
                                   dict(matches[0]))

    def write(self, command: Command, payload: Any) -> Mapping[str, Any]:
        require(isinstance(command, Command) and command.media_type == "album"
                and isinstance(payload, Mapping)
                and payload.get("foreignAlbumId") == command.authority_id,
                "acquisition-lidarr-payload")
        body = dict(payload)
        body.update({"rootFolderPath": self.root,
                     "qualityProfileId": self.quality,
                     "metadataProfileId": self.metadata,
                     "monitored": True,
                     "addOptions": {"monitor": "all",
                                    "searchForNewAlbum": True}})
        artist = dict(body.get("artist") or {})
        artist.update({"rootFolderPath": self.root,
                       "qualityProfileId": self.quality,
                       "metadataProfileId": self.metadata,
                       "monitored": False,
                       "monitorNewItems": "none",
                       "addOptions": {"monitor": "none",
                                      "searchForMissingAlbums": False}})
        body["artist"] = artist
        status, result = self.transport("POST", "/api/v1/album", None, body)
        require(status in (200, 201) and isinstance(result, Mapping)
                and type(result.get("id")) in (str, int)
                and type(result.get("id")) is not bool,
                "acquisition-lidarr-write")
        return {"status": "processing", "request_id": result["id"]}


class LazyLibrarianProvider:
    def __init__(self, transport: Transport):
        require(callable(transport), "acquisition-lazy-configuration")
        self.transport = transport

    @staticmethod
    def _id(command):
        return command.authority_id.rsplit("/", 1)[-1]

    def revalidate(self, command: Command) -> AuthorityResolution:
        require(isinstance(command, Command)
                and command.media_type in ("ebook", "audiobook")
                and command.authority == "openlibrary",
                "acquisition-lazy-command")
        status, value = self.transport(
            "GET", "/api", {"cmd": "getAllBooks", "json": "1"}, None)
        require(status == 200, "acquisition-lazy-read")
        books = value.get("books", []) if isinstance(value, Mapping) else value
        require(isinstance(books, list), "acquisition-lazy-read")
        identity = self._id(command)
        matches = [book for book in books if isinstance(book, Mapping)
                   and str(book.get("BookID", book.get("bookid", ""))).rsplit(
                       "/", 1)[-1] == identity]
        require(len(matches) <= 1, "acquisition-lazy-existing-ambiguous")
        if matches:
            book = matches[0]
            title = str(book.get("BookName", book.get("bookname", ""))).strip()
            require(title.casefold() == command.title.casefold(),
                    "acquisition-lazy-identity-changed")
            keys = (("AudioStatus", "audiostatus")
                    if command.media_type == "audiobook"
                    else ("Status", "status"))
            states = {str(book.get(key, "")).casefold() for key in keys}
            if states & {"wanted", "have", "open", "snatched"}:
                return AuthorityResolution(command.identity, "available")
        return AuthorityResolution(command.identity, "requestable", identity)

    def write(self, command: Command, payload: Any) -> Mapping[str, Any]:
        identity = self._id(command)
        require(isinstance(command, Command)
                and command.media_type in ("ebook", "audiobook")
                and payload == identity,
                "acquisition-lazy-payload")
        status, added = self.transport(
            "GET", "/api",
            {"cmd": "addBook", "id": identity, "wait": "1",
             "source": "OpenLibrary"}, None)
        require(status == 200 and added is not False,
                "acquisition-lazy-add")
        status, queued = self.transport(
            "GET", "/api",
            {"cmd": "queueBook", "id": identity,
             "type": "AudioBook" if command.media_type == "audiobook"
             else "eBook"}, None)
        require(status == 200 and queued == "OK", "acquisition-lazy-queue")
        return {"status": "processing", "request_id": identity}
