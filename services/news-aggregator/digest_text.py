"""Shared digest cleanup for story deduplication and speech formatting."""
import re
from difflib import SequenceMatcher
from typing import Optional

STOPWORDS = {"the", "a", "an", "of", "to", "in", "on", "for", "is", "are", "be", "and", "or", "with", "as", "by", "it", "its", "at", "from", "that", "this", "says", "said", "will", "has", "have", "had", "after", "over", "new", "what", "how", "why", "who", "you", "your", "former", "launch", "launched", "launches", "file", "files", "filed", "legal", "action", "court", "police", "report", "reports", "according", "officials", "following", "amid", "ongoing", "current", "latest"}

def _keywords(title: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9']{3,}", title.lower()) if word not in STOPWORDS}

def same_story(title_a: str, title_b: str, body_a: str = "", body_b: str = "") -> bool:
    if SequenceMatcher(None, title_a.lower(), title_b.lower()).ratio() >= 0.70:
        return True
    words_a, words_b = _keywords(title_a), _keywords(title_b)
    overlap = words_a & words_b
    if len(overlap) >= 3 and len(overlap) / len(words_a | words_b) >= 0.35:
        return True
    if body_a and body_b:
        body_words_a = _keywords(f"{title_a} {body_a}")
        body_words_b = _keywords(f"{title_b} {body_b}")
        body_overlap = body_words_a & body_words_b
        return len(body_overlap) >= 5 and len(body_overlap) / len(body_words_a | body_words_b) >= 0.12
    return False

def repeat_story(title_a: str, title_b: str) -> bool:
    """Match the same event across separate briefings conservatively."""
    if SequenceMatcher(None, title_a.lower(), title_b.lower()).ratio() >= 0.78:
        return True
    words_a, words_b = _keywords(title_a), _keywords(title_b)
    overlap = words_a & words_b
    return len(overlap) >= 4 and len(overlap) / len(words_a | words_b) >= 0.28

def coherent_event(records: list, title_key: str = "title") -> list:
    """Return the largest clearly coherent subgroup in a cluster."""
    groups = []
    for record in records:
        title = record[title_key]
        for group in groups:
            if any(repeat_story(title, prior[title_key]) for prior in group):
                group.append(record)
                break
        else:
            groups.append([record])
    return max(groups, key=len, default=[])

def dedupe_titles(records: list, title_key: str = "title", text_key: Optional[str] = None) -> list:
    kept = []
    for record in records:
        body = record[text_key] if text_key else ""
        if not any(same_story(record[title_key], prior[title_key], body, prior[text_key] if text_key else "") for prior in kept):
            kept.append(record)
    return kept

_DOLLAR_AMOUNT = re.compile(r"(?<!\w)(?:(US|CA|AU)\s*)?\$(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?:\s+(million|billion|trillion))?\b", re.IGNORECASE)
_US_ABBREVIATION = re.compile(r"\bU\.S(?:\.A)?\.(?=\s|$|[,;:!?])", re.IGNORECASE)

def speech_text(text: str) -> str:
    """Turn LLM/Markdown prose into text Piper should read aloud."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text).replace("*", "")
    text = re.sub(r"(?<!\w)_+(?!\w)", "", text)
    # Kokoro inserts a long pause when it sees dotted initials. Expand these
    # to the spoken name so headlines such as "U.S. suspect" flow naturally.
    text = _US_ABBREVIATION.sub("United States", text)
    text = _DOLLAR_AMOUNT.sub(lambda m: f"{m.group(2)}{'.' + m.group(3) if m.group(3) else ''} {m.group(4) + ' ' if m.group(4) else ''}{m.group(1) + ' ' if m.group(1) else ''}dollars", text)
    text = text.replace("(", ", ").replace(")", ", ")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r",([.!?])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip(" ,")
