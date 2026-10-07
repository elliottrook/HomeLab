"""Provider-neutral, deterministic ranking for the unified recommendation portal.

Providers are deliberately kept outside this module. They return sanitized
candidate dictionaries; this engine handles identity, suppression, scoring and
the user-facing explanation fields. No network or write operation belongs here.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable, Mapping


_SOURCE_WEIGHTS = {
    "seerr": 0.70,
    "tmdb": 0.70,
    "lidarr": 0.66,
    "musicbrainz": 0.62,
    "listenbrainz": 0.62,
    "lastfm": 0.60,
    "openlibrary": 0.60,
    "googlebooks": 0.60,
    "audiobookshelf": 0.58,
}


def _fold(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def identity_key(item: Mapping[str, Any]) -> tuple[str, str]:
    """Return a conservative cross-provider identity key."""
    return (_fold(item.get("media_type")), _fold(item.get("title")))


def _as_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    # TMDb-style ratings are on a ten-point scale; internal scores are 0..1.
    if score > 1.0:
        score /= 10.0
    return max(0.0, min(1.0, score))


def _source_weight(item: Mapping[str, Any]) -> float:
    authority = _fold(item.get("authority"))
    return _SOURCE_WEIGHTS.get(authority, 0.50)


def _library_index(library: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    indexed: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for item in library:
        if isinstance(item, Mapping) and item.get("title"):
            indexed[identity_key(item)].append(item)
    return indexed


def _history_profile(history: Iterable[Mapping[str, Any]]) -> tuple[set[str], set[str]]:
    titles: set[str] = set()
    genres: set[str] = set()
    for item in history:
        if not isinstance(item, Mapping):
            continue
        if item.get("title"):
            titles.add(_fold(item["title"]))
        values = item.get("genres")
        if isinstance(values, (list, tuple, set)):
            genres.update(_fold(value) for value in values if value)
    return titles, {genre for genre in genres if genre}


def rank_candidates(
    candidates: Iterable[Mapping[str, Any]],
    *,
    library: Iterable[Mapping[str, Any]] = (),
    history: Iterable[Mapping[str, Any]] = (),
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Rank safe candidates without guessing ambiguous identity.

    The returned dictionaries are copies. A candidate matching more than one
    provider identity is excluded, as are active/archive library matches. The
    ranking is intentionally explainable: source quality, provider score,
    genre overlap and history absence are all explicit fields.
    """
    owned = _library_index(library)
    history_titles, history_genres = _history_profile(history)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw in candidates:
        if not isinstance(raw, Mapping) or not raw.get("title") or not raw.get("media_type"):
            continue
        item = dict(raw)
        grouped[identity_key(item)].append(item)

    ranked: list[dict[str, Any]] = []
    for key, matches in grouped.items():
        # A same-title result from multiple providers is not safe to action
        # until the adapter supplies an explicit canonical identity.
        ids = {(str(item.get("authority", "")), str(item.get("authority_id", ""))) for item in matches}
        ambiguous = len(ids) > 1 or any(item.get("match_count", 1) != 1 for item in matches)
        item = max(matches, key=lambda value: (_as_score(value.get("score")), str(value.get("authority_id", ""))))
        item["match_count"] = 2 if ambiguous else 1
        library_matches = owned.get(key, [])
        item["owned"] = bool(item.get("owned")) or any(not match.get("archived") for match in library_matches)
        item["archived"] = bool(item.get("archived")) or any(bool(match.get("archived")) for match in library_matches)
        signals = [str(signal) for signal in item.get("signals", ()) if signal]
        genre_values = item.get("genres") if isinstance(item.get("genres"), list) else []
        genre_overlap = sorted({_fold(value) for value in genre_values if _fold(value) in history_genres})
        if genre_overlap:
            signals.append("matches genres from your listening or viewing history")
        if _fold(item.get("title")) in history_titles:
            signals.append("matches a title already present in your history")
        if not library_matches:
            signals.append("is not in the active or archive library")
        signals = list(dict.fromkeys(signals))
        item["signals"] = signals
        item["score"] = round(
            (_as_score(item.get("score")) * 0.60)
            + (_source_weight(item) * 0.25)
            + (0.15 if genre_overlap else 0.0),
            6,
        )
        item["explanation"] = _explanation(item, signals, ambiguous)
        if item["match_count"] == 1 and not item["owned"] and not item["archived"]:
            ranked.append(item)

    ranked.sort(key=lambda item: (-item["score"], str(item.get("media_type")), _fold(item.get("title")), str(item.get("authority_id", ""))))
    return ranked[:max(0, int(limit))]


def _explanation(item: Mapping[str, Any], signals: list[str], ambiguous: bool) -> str:
    if ambiguous:
        return "Held back because provider identity is ambiguous; no request action is offered."
    source = str(item.get("source_label") or item.get("authority") or "configured source")
    if signals:
        return f"Suggested by {source}: " + "; ".join(signals) + "."
    return f"Suggested by {source}; it is not in the active or archive library."
