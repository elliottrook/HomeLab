"""Idempotently add the private recommendations portal to Homepage."""

from pathlib import Path


path = Path("/opt/homepage/config/services.yaml")
text = path.read_text(encoding="utf-8")
name = "    - Unified Media Recommendations:\n"
if name not in text:
    anchor = (
        "    - Aster Knowledge Wiki:\n"
        "        icon: mdi-book-lock-outline\n"
        "        href: https://wiki.elliottrook.com\n"
        "        description: Private human knowledge intake and source portal\n"
    )
    if text.count(anchor) != 1:
        raise RuntimeError("expected unique Aster Knowledge Wiki Homepage anchor is missing")
    addition = anchor + "\n" + name + (
        "        icon: mdi-movie-open-star-outline\n"
        "        href: https://recommendations.elliottrook.com\n"
        "        description: Private AI-assisted media recommendations and requests\n"
    )
    text = text.replace(anchor, addition)
    temporary = path.with_name(path.name + ".unified-media.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
print("unified-media-homepage=present")
