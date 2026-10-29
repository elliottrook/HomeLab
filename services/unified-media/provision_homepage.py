"""Idempotently add the private recommendations portal to Homepage."""

from pathlib import Path


path = Path("/opt/homepage/config/services.yaml")
text = path.read_text(encoding="utf-8")
name = "    - Media Acquisition Hub:\n"
legacy_name = "    - Unified Media Recommendations:\n"
for old in (name, legacy_name):
    if old in text:
        start = text.index(old)
        next_tile = text.find("\n    - ", start + len(old))
        next_section = text.find("\n- ", start + len(old))
        positions = [pos for pos in (next_tile, next_section) if pos != -1]
        end = min(positions) if positions else len(text)
        text = text[:start] + text[end + 1:]
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
        "        icon: https://recommendations.elliottrook.com/icon-512.png?v=b4cc2938\n"
        "        href: https://recommendations.elliottrook.com\n"
        "        description: Private AI-assisted media recommendations and requests\n"
    )
    text = text.replace(anchor, addition)
    temporary = path.with_name(path.name + ".unified-media.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
print("media-acquisition-hub-homepage=present")
