"""Sanitized, credential-free wire contract between AsterTV and Seerr broker."""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping


KINDS = frozenset(("movie", "tv"))
IDENTITY = re.compile(r"^seerr:(movie|tv):([1-9][0-9]{0,9})$")
AVAILABILITY = {
    1: "unknown", 2: "pending", 3: "processing", 4: "partial",
    5: "available", 6: "blocklisted", 7: "deleted",
}
REQUEST_STATE = {1: "pending", 2: "approved", 3: "declined",
                 4: "failed", 5: "available"}


class ContractError(ValueError):
    pass


def require(value: bool, code: str) -> None:
    if not value:
        raise ContractError(code)


def text(value: Any, maximum: int, *, required: bool = False) -> str:
    require(isinstance(value, str), "seerr-text-invalid")
    value = unicodedata.normalize("NFC", " ".join(value.split()))
    require(not any(unicodedata.category(char).startswith("C") for char in value)
            and len(value) <= maximum and (bool(value) or not required),
            "seerr-text-invalid")
    return value


def _request(media: Mapping[str, Any]) -> tuple[object, str]:
    requests = media.get("requests") or []
    require(isinstance(requests, list) and len(requests) <= 100,
            "seerr-requests-invalid")
    valid = [item for item in requests if isinstance(item, Mapping)
             and type(item.get("id")) is int and item["id"] > 0
             and type(item.get("status")) is int
             and item["status"] in REQUEST_STATE]
    if not valid:
        return None, "none"
    latest = max(valid, key=lambda item: item["id"])
    return latest["id"], REQUEST_STATE[latest["status"]]


def candidate(item: Mapping[str, Any], detail: Mapping[str, Any]) -> dict[str, Any]:
    require(isinstance(item, Mapping) and isinstance(detail, Mapping),
            "seerr-candidate-invalid")
    kind = str(item.get("mediaType") or item.get("media_type") or "")
    media_id = item.get("id")
    require(kind in KINDS and type(media_id) is int and 0 < media_id <= 9_999_999_999,
            "seerr-candidate-identity")
    title = text(str(item.get("title") or item.get("name") or ""), 200, required=True)
    date = str(item.get("releaseDate") or item.get("firstAirDate") or "")
    year = date[:4] if re.match(r"^[12][0-9]{3}", date) else ""
    overview = text(str(item.get("overview") or ""), 3000)
    poster = str(item.get("posterPath") or item.get("poster_path") or "")
    require(len(poster) <= 300 and (not poster or poster.startswith("/")),
            "seerr-poster-invalid")
    poster = "https://image.tmdb.org/t/p/w500" + poster if poster else ""
    media = detail.get("mediaInfo") or item.get("mediaInfo") or {}
    require(isinstance(media, Mapping), "seerr-media-invalid")
    raw_status = media.get("status", 1)
    require(type(raw_status) is int and raw_status in AVAILABILITY,
            "seerr-media-status-invalid")
    availability = AVAILABILITY[raw_status]
    request_id, request_state = _request(media)
    if availability == "available":
        request_state = "available"
    elif availability in ("pending", "processing", "partial") and request_id:
        request_state = "processing"
    elif availability == "blocklisted" and request_id:
        request_state = "failed"
    seasons = []
    if kind == "tv":
        raw_seasons = detail.get("seasons") or []
        require(isinstance(raw_seasons, list) and len(raw_seasons) <= 999,
                "seerr-seasons-invalid")
        seasons = sorted({row["seasonNumber"] for row in raw_seasons
                          if isinstance(row, Mapping)
                          and type(row.get("seasonNumber")) is int
                          and 1 <= row["seasonNumber"] <= 999})
    return {
        "schema": 2, "identity": f"seerr:{kind}:{media_id}",
        "media_type": kind, "media_id": media_id, "title": title,
        "year": year, "overview": overview, "poster": poster,
        "owned": availability in ("partial", "available"),
        "availability": availability, "request_id": request_id,
        "request_state": request_state, "seasons": seasons,
    }


def page(query: str, media_type: str, rows: list[tuple[Mapping[str, Any], Mapping[str, Any]]]) -> dict[str, Any]:
    query = text(query, 100, required=True)
    require(media_type in KINDS | {"all"} and isinstance(rows, list)
            and len(rows) <= 24, "seerr-page-invalid")
    candidates = [candidate(item, detail) for item, detail in rows]
    if media_type != "all":
        require(all(item["media_type"] == media_type for item in candidates),
                "seerr-page-type-invalid")
    require(len({item["identity"] for item in candidates}) == len(candidates),
            "seerr-page-duplicate")
    return {"schema": 1, "query": query, "candidates": candidates}


def proposal(value: Any) -> dict[str, Any]:
    required = {"schema", "action", "authority", "candidate_id", "media_type",
                "media_id", "seasons", "confirmed"}
    require(type(value) is dict and set(value) == required and value["schema"] == 1
            and value["action"] == "request" and value["authority"] == "seerr"
            and value["confirmed"] is True, "seerr-proposal-invalid")
    identity = value["candidate_id"]
    match = IDENTITY.fullmatch(identity) if isinstance(identity, str) else None
    kind, media_id = value["media_type"], value["media_id"]
    require(match is not None and kind in KINDS and match.group(1) == kind
            and type(media_id) is int and int(match.group(2)) == media_id,
            "seerr-proposal-identity")
    seasons = value["seasons"]
    require(type(seasons) is list and seasons == sorted(set(seasons))
            and all(type(season) is int and 1 <= season <= 999 for season in seasons)
            and ((kind == "movie" and not seasons) or (kind == "tv" and seasons)),
            "seerr-proposal-seasons")
    return dict(value)


def request_result(raw: Mapping[str, Any], expected: str, *, duplicate: bool) -> dict[str, Any]:
    require(isinstance(raw, Mapping) and IDENTITY.fullmatch(expected) is not None,
            "seerr-result-invalid")
    request_id, request_status = raw.get("id"), raw.get("status")
    require(type(request_id) is int and request_id > 0
            and type(request_status) is int and request_status in REQUEST_STATE,
            "seerr-result-invalid")
    return {"schema": 1, "candidate_id": expected, "request_id": request_id,
            "state": REQUEST_STATE[request_status], "duplicate": bool(duplicate)}
