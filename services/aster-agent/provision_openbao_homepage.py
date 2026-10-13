"""Idempotently add the safe OpenBao recovery deep-link to Homepage.

The tile opens the authenticated Aster Companion panel. It never links to the
OpenBao listener, broker socket or a secrets-management UI.
"""

from pathlib import Path


path = Path("/opt/homepage/config/services.yaml")
text = path.read_text(encoding="utf-8")
name = "    - OpenBao Recovery:\n"
if name not in text:
    anchor = "    - Aster Companion:\n"
    start = text.find(anchor)
    if start < 0:
        raise RuntimeError("expected Aster Companion Homepage anchor is missing")
    end = text.find("\n    - ", start + len(anchor))
    if end < 0:
        end = len(text)
    addition = (
        "\n    - OpenBao Recovery:\n"
        "        icon: mdi-lock-reset\n"
        "        href: https://aster.elliottrook.com/companion#openbao\n"
        "        description: Passkey-protected human unseal recovery\n"
    )
    text = text[:end] + addition + text[end:]
    temporary = path.with_name(path.name + ".openbao-recovery.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)

print("openbao-recovery-homepage=present")
