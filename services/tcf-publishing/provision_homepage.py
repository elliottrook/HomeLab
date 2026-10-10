"""Idempotently place the private Photography Content Desk in Homepage."""

from pathlib import Path


path = Path("/opt/homepage/config/services.yaml")
text = path.read_text(encoding="utf-8")
name = "    - Photography Content Desk:\n"
icon = "https://tcf.elliottrook.com/app-icon-512.png?v=f1b7a949"
tile = name + (
    f"        icon: {icon}\n"
    "        href: https://tcf.elliottrook.com\n"
    "        description: Private dual-site photography editing and publication\n"
)

# Remove an existing copy wherever it currently lives so section changes are
# reconciled rather than creating a duplicate tile.
if name in text:
    start = text.index(name)
    next_tile = text.find("\n    - ", start + len(name))
    next_section = text.find("\n- ", start + len(name))
    candidates = [position for position in (next_tile, next_section) if position != -1]
    end = min(candidates) if candidates else len(text)
    text = text[:start] + text[end + 1:]

section = "- Application Management:\n"
next_section = "- External Services:\n"
if text.count(section) != 1 or text.count(next_section) != 1:
    raise RuntimeError("expected unique Application Management section is missing")
insert_at = text.index(next_section)
updated = text[:insert_at].rstrip() + "\n\n" + tile + "\n" + text[insert_at:]

temporary = path.with_name(path.name + ".tcf.tmp")
temporary.write_text(updated, encoding="utf-8")
temporary.replace(path)
print("tcf-content-desk-homepage=application-management")
