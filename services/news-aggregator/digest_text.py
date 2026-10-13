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
_US_ABBREVIATION = re.compile(r"\bU\.S(?:\.A)?\.(?=(?:['’]s)?(?:\s|$|[,;:!?]))", re.IGNORECASE)
_BC_ABBREVIATION = re.compile(r"\bB\.C\.(?=(?:['’]s)?(?:\s|$|[,;:!?]))", re.IGNORECASE)
_LUTRON_CASETA = re.compile(r"\bLutron Cas[eé]ta\b", re.IGNORECASE)

_ONES = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
)
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_CURRENCY_NAMES = {"US": "United States", "CA": "Canadian", "AU": "Australian"}


def _under_thousand(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")
    hundreds, remainder = divmod(n, 100)
    return f"{_ONES[hundreds]} hundred" + (f" and {_under_thousand(remainder)}" if remainder else "")


def _integer_words(n: int) -> str:
    if n < 1000:
        return _under_thousand(n)
    parts = []
    for value, name in ((10**12, "trillion"), (10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        chunk, n = divmod(n, value)
        if chunk:
            parts.append(f"{_under_thousand(chunk)} {name}")
    if n:
        joiner = " and " if n < 100 else " "
        return " ".join(parts) + joiner + _under_thousand(n)
    return " ".join(parts)


def _spoken_currency(match: re.Match) -> str:
    country = (match.group(1) or "").upper()
    whole = int(match.group(2).replace(",", ""))
    fraction = match.group(3)
    magnitude = match.group(4)
    prefix = f"{_CURRENCY_NAMES[country]} " if country else ""
    if magnitude:
        amount = _integer_words(whole)
        if fraction:
            amount += " point " + " ".join(_ONES[int(digit)] for digit in fraction)
        return f"{amount} {magnitude.lower()} {prefix}dollars"
    dollars = "dollar" if whole == 1 and not fraction else "dollars"
    spoken = f"{_integer_words(whole)} {prefix}{dollars}"
    if fraction:
        cents = int((fraction + "0")[:2])
        if cents:
            spoken += f" and {_integer_words(cents)} {'cent' if cents == 1 else 'cents'}"
    return spoken


def _apply_pronunciations(text: str) -> str:
    """Canonicalize approved product spelling without phonetic substitutions."""
    return _LUTRON_CASETA.sub("Lutron Caseta", text)


def _expand_dotted_name(match: re.Match, name: str) -> str:
    """Retain the shared final dot when an abbreviation ends the sentence."""
    return name + ("." if match.end() == len(match.string) else "")

def speech_text(text: str) -> str:
    """Turn LLM/Markdown prose into text Piper should read aloud."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text).replace("*", "")
    text = re.sub(r"(?<!\w)_+(?!\w)", "", text)
    # Kokoro inserts a long pause when it sees dotted initials. Expand these
    # to the spoken name so headlines such as "U.S. suspect" flow naturally.
    text = _US_ABBREVIATION.sub(lambda match: _expand_dotted_name(match, "United States"), text)
    text = _BC_ABBREVIATION.sub(lambda match: _expand_dotted_name(match, "British Columbia"), text)
    text = _DOLLAR_AMOUNT.sub(_spoken_currency, text)
    text = text.replace("(", ", ").replace(")", ", ")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r",([.!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" ,")
    return _apply_pronunciations(text)
