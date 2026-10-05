"""Deterministic, fail-closed recommendation primitives for M3."""

from dataclasses import dataclass, field
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Recommendation:
    media_type: str
    authority: str
    authority_id: str
    title: str
    score: float
    signals: Tuple[str, ...] = field(default_factory=tuple)
    owned: bool = False
    archived: bool = False
    match_count: int = 1


def rank_recommendations(items: Iterable[Recommendation], limit: int = 20) -> list:
    """Return safe candidates in deterministic score/title order.

    Unknown or unsafe identity state is excluded rather than guessed. This is
    intentionally independent of an LLM; narration can be layered on later.
    """
    safe = [item for item in items if item.match_count == 1 and not item.owned and not item.archived]
    safe.sort(key=lambda item: (-item.score, item.media_type, item.title.casefold(), item.authority_id))
    return safe[:max(0, limit)]


def explain(item: Recommendation) -> str:
    if not item.signals:
        return "Recommended from the current library and preference snapshot."
    return "Recommended because " + "; ".join(item.signals) + "."
