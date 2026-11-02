"""Pure validation helpers for the Aster actor-search plug-in."""


def clean_actor(value):
    raw = value or ""
    if any(ord(char) < 32 for char in raw):
        raise ValueError("invalid actor query")
    actor = " ".join(raw.split())
    if not actor or len(actor) > 128:
        raise ValueError("invalid actor query")
    return actor
