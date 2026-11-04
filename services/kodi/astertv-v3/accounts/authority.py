#!/usr/bin/env python3
"""Build the local recovery-admin registry from resolved Jen identities."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from identity_resolver import discover
from registry import validate


AUTHORITY_FIELDS = {"schema", "recovery_admin_display_name", "profile_id"}
PROFILE_ID = re.compile(r"^[a-z][a-z0-9-]{0,47}$")


class AuthorityError(ValueError):
    pass


def load_authority(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError) as error:
        raise AuthorityError("authority-config-unavailable") from error
    if not isinstance(value, dict) or set(value) != AUTHORITY_FIELDS:
        raise AuthorityError("authority-config-fields")
    if value["schema"] != 1:
        raise AuthorityError("authority-config-schema")
    if (not isinstance(value["recovery_admin_display_name"], str)
            or not value["recovery_admin_display_name"].strip()):
        raise AuthorityError("authority-display-name")
    if not isinstance(value["profile_id"], str) or not PROFILE_ID.fullmatch(value["profile_id"]):
        raise AuthorityError("authority-profile-id")
    return copy.deepcopy(value)


def build_registry(authority, updated_at, root=Path("/")):
    subjects = discover(root)
    mappings = []
    for service in ("jellyfin", "audiobookshelf", "seerr"):
        subject = subjects.get(service)
        if subject:
            mappings.append({
                "service": service,
                "opaque_subject_id": subject,
                "enabled": True,
            })
    entitlements = ["clock", "local_settings_read", "profile_admin"]
    if "jellyfin" in subjects:
        entitlements.extend([
            "public_catalogue_browse", "viewing_history",
            "personal_recommendations", "listening_history",
        ])
    if "audiobookshelf" in subjects:
        entitlements.extend(["books_private", "listening_history"])
    if "seerr" in subjects:
        entitlements.append("requests_submit")
    registry = {
        "schema": 1,
        "active_profile_id": "guest",
        "profiles": [{
            "id": authority["profile_id"],
            "display_name": authority["recovery_admin_display_name"],
            "role": "recovery_admin",
            "service_mappings": mappings,
            "entitlements": sorted(set(entitlements)),
            "preferences": {"clock": "24h", "captions": False},
        }, {
            "id": "guest",
            "display_name": "Guest",
            "role": "guest",
            "service_mappings": [],
            "entitlements": ["public_catalogue_browse", "clock", "local_settings_read"],
            "preferences": {"clock": "24h", "captions": False},
        }],
        "updated_at": updated_at,
    }
    return validate(registry)
