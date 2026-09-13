"""Idempotently add the authenticated Aster Wiki link to Homepage."""

from pathlib import Path

path = Path("/opt/homepage/config/services.yaml")
text = path.read_text(encoding="utf-8")
name = "    - Aster Knowledge Wiki:\n"
if name not in text:
    anchor = (
        "    - Aster Agent:\n"
        "        icon: mdi-robot-outline\n"
        "        href: http://192.168.70.10:9120\n"
        "        description: Local AI assistant API and browser UI\n"
    )
    if text.count(anchor) != 1:
        raise RuntimeError("expected unique Aster Agent Homepage anchor is missing")
    addition = (
        anchor
        + "\n"
        + name
        + "        icon: mdi-book-lock-outline\n"
        + "        href: https://wiki.elliottrook.com\n"
        + "        description: Private human knowledge intake and source portal\n"
    )
    text = text.replace(anchor, addition)
    temporary = path.with_name(path.name + ".aster-wiki.tmp")
    temporary = path.with_name(path.name + ".aster-wiki.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)

print("aster-wiki-homepage=present")
