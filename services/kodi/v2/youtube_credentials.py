"""Secret-safe configuration model for the official Kodi YouTube add-on.

This module never logs or renders credential values.  The caller is responsible
for collecting them through a hidden local prompt and for writing the returned
document only to the add-on's protected per-client state.
"""

from __future__ import annotations

import json


PERSONAL_FIELDS = ("api_key", "client_id", "client_secret")
CLIENT_SUFFIX = ".apps.googleusercontent.com"


class CredentialError(ValueError):
    pass


def _clean(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise CredentialError(f"{field}-must-be-text")
    value = value.strip()
    if not value or any(ch in value for ch in "\r\n\0"):
        raise CredentialError(f"{field}-missing-or-multiline")
    return value


def normalize(api_key: str, client_id: str, client_secret: str) -> dict[str, str]:
    values = {
        "api_key": _clean(api_key, "api-key"),
        "client_id": _clean(client_id, "client-id"),
        "client_secret": _clean(client_secret, "client-secret"),
    }
    if values["client_id"].endswith(CLIENT_SUFFIX):
        values["client_id"] = values["client_id"][: -len(CLIENT_SUFFIX)]
    if not values["client_id"]:
        raise CredentialError("client-id-empty-after-normalization")
    return values


def configure(existing: bytes, credentials: dict[str, str]) -> bytes:
    try:
        document = json.loads(existing.decode("utf-8")) if existing.strip() else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CredentialError("existing-api-key-document-invalid") from error
    if not isinstance(document, dict):
        raise CredentialError("existing-api-key-document-not-object")
    keys = document.setdefault("keys", {})
    if not isinstance(keys, dict):
        raise CredentialError("existing-keys-not-object")
    supplied = {field: _clean(credentials.get(field, ""), field.replace("_", "-"))
                for field in PERSONAL_FIELDS}
    # v7.4.4 migrates the documented ``personal`` key to ``user`` only when
    # ``user`` does not already exist.  Established installs already contain
    # an empty ``user`` slot, so writing only ``personal`` leaves Kodi reading
    # empty credentials.  Store the canonical runtime key directly and avoid
    # retaining a second copy of the secrets.
    keys["user"] = supplied
    keys.pop("personal", None)
    keys.setdefault("developer", {})
    return (json.dumps(document, indent=4, sort_keys=True) + "\n").encode("utf-8")


def configured(document: bytes) -> bool:
    try:
        personal = json.loads(document.decode("utf-8")).get("keys", {}).get("user", {})
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return isinstance(personal, dict) and all(
        isinstance(personal.get(field), str) and bool(personal[field].strip())
        for field in PERSONAL_FIELDS
    )

