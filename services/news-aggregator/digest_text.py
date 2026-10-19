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
_ABBREVIATION_END = r"(?=(?:['’]s)?(?:\s|$|[-–—,;:!?]))"
_US_ABBREVIATION = re.compile(rf"\bU\.S(?:\.A)?\.{_ABBREVIATION_END}", re.IGNORECASE)
_BC_ABBREVIATION = re.compile(rf"\bB\.C\.{_ABBREVIATION_END}", re.IGNORECASE)
_SAINT_PETERSBURG = re.compile(r"\bSt\.\s+Petersburg\b", re.IGNORECASE)
_GROUPED_INTEGER = re.compile(
    r"(?<!\w)\d{1,3}(?:[,.]\d{3})+(?!\d|[,.]\d)"
    r"(?!\s*(?:%|percent\b|million\b|billion\b|trillion\b))",
    re.IGNORECASE,
)
_LUTRON_CASETA = re.compile(r"\bLutron Cas[eé]ta\b", re.IGNORECASE)
_EMERGENCY_911 = re.compile(
    r"\b911\b(?=\s+(?:call|calls|caller|callers|dispatch|dispatcher|dispatchers|"
    r"operator|operators|service|services|emergency|centre|center)\b)",
    re.IGNORECASE,
)
_ROMAN_NUMERAL = re.compile(r"(?<![A-Za-z])(?=[IVX]{2,5}(?![A-Za-z]))[IVX]+")
_BARE_URL = re.compile(
    r"(?<!\w)(?:https?://|www\.)[^\s<>()]+|"
    r"(?<![@\w])(?:[a-z0-9-]+\.)+(?:com|org|net|ca|co\.uk)(?:/[^\s<>()]*)?",
    re.IGNORECASE,
)

_ONES = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
)

_ORDINALS = (
    "", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth",
    "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth",
    "nineteenth", "twentieth", "twenty-first", "twenty-second", "twenty-third",
    "twenty-fourth", "twenty-fifth", "twenty-sixth", "twenty-seventh",
    "twenty-eighth", "twenty-ninth", "thirtieth", "thirty-first",
)


def spoken_ordinal(day: int) -> str:
    """Return an unambiguous spoken calendar ordinal."""
    if not 1 <= day <= 31:
        raise ValueError("calendar day must be between 1 and 31")
    return _ORDINALS[day]


def _spoken_roman(match: re.Match) -> str:
    values = {"I": 1, "V": 5, "X": 10}
    total = previous = 0
    for character in reversed(match.group(0)):
        value = values[character]
        total += -value if value < previous else value
        previous = max(previous, value)
    if not 2 <= total <= 39:
        return match.group(0)
    return _integer_words(total)
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


def _speak_grouped_integer(match: re.Match) -> str:
    raw = match.group(0)
    separators = {character for character in raw if character in ",."}
    if len(separators) != 1:
        return raw
    return _integer_words(int(raw.replace(next(iter(separators)), "")))


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
    text = _BARE_URL.sub(
        lambda match: match.group(0)[-1] if match.group(0)[-1] in ".,!?:;" else "",
        text,
    )
    text = re.sub(r"`([^`]*)`", r"\1", text).replace("*", "")
    text = re.sub(r"(?<!\w)_+(?!\w)", "", text)
    # Kokoro inserts a long pause when it sees dotted initials. Expand these
    # to the spoken name so headlines such as "U.S. suspect" flow naturally.
    text = _US_ABBREVIATION.sub(lambda match: _expand_dotted_name(match, "United States"), text)
    text = _BC_ABBREVIATION.sub(lambda match: _expand_dotted_name(match, "British Columbia"), text)
    text = _SAINT_PETERSBURG.sub("Saint Petersburg", text)
    text = _EMERGENCY_911.sub("nine one one", text)
    text = _ROMAN_NUMERAL.sub(_spoken_roman, text)
    text = _DOLLAR_AMOUNT.sub(_spoken_currency, text)
    # Kokoro can read grouped digits one by one. Accept English and European
    # thousands separators without rewriting ordinary decimal measurements.
    text = _GROUPED_INTEGER.sub(_speak_grouped_integer, text)
    text = text.replace("(", ", ").replace(")", ", ")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r",([.!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" ,")
    return _apply_pronunciations(text)


def narration_units(text: str, maximum: int = 220) -> list[tuple[str, float]]:
    """Create bounded long-form units with an explicit pause after each one."""
    if maximum < 80:
        raise ValueError("maximum narration unit length is too small")
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    units: list[tuple[str, float]] = []
    for sentence in sentences:
        pending = sentence.strip()
        if not pending:
            continue
        while len(pending) > maximum:
            cut = max(pending.rfind(mark, 0, maximum + 1) for mark in ("; ", ": ", ", "))
            if cut < maximum // 2:
                cut = pending.rfind(" ", 0, maximum + 1)
            if cut < 1:
                cut = maximum
            unit = pending[:cut].rstrip(" ,;:")
            if unit:
                units.append((unit, 0.08))
            pending = pending[cut:].lstrip(" ,;:")
        if pending:
            units.append((pending, 0.18))
    if units:
        units[-1] = (units[-1][0], 0.0)
    return units
