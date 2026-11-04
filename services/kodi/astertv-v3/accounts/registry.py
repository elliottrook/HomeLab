#!/usr/bin/env python3
"""Credential-free AsterTV profile registry with fail-closed recovery."""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from pathlib import Path


ROOT_FIELDS = {"schema", "active_profile_id", "profiles", "updated_at"}
PROFILE_FIELDS = {
    "id", "display_name", "role", "service_mappings", "entitlements", "preferences"
}
MAPPING_FIELDS = {"service", "opaque_subject_id", "enabled"}
ROLES = {"recovery_admin", "member", "guest"}
SERVICES = {"jellyfin", "audiobookshelf", "youtube", "seerr", "home_assistant", "aster"}
ENTITLEMENTS = {
    "fixture_catalogue", "fixture_listening", "public_catalogue_browse",
    "clock", "local_settings_read", "personal_youtube", "requests_submit",
    "books_private", "viewing_history", "personal_recommendations",
    "listening_history", "home_control", "cameras",
    "aster_private_context", "profile_admin",
}
PREFERENCES = {"clock", "captions"}
DENIED_GUEST = {
    "personal_youtube", "requests_submit", "books_private", "listening_history",
    "viewing_history", "personal_recommendations", "home_control", "cameras",
    "aster_private_context", "profile_admin",
}
SECRET_NAMES = {
    "password", "passphrase", "token", "api_key", "secret", "cookie",
    "oauth_code", "refresh_token", "access_token", "credential",
}
ID = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
SYNTHETIC_SUBJECT = re.compile(r"^synthetic:[a-z0-9-]+:[a-z0-9-]+$")
RFC3339_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class RegistryError(ValueError):
    pass


def _reject_secret_names(value, path="root"):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in SECRET_NAMES:
                raise RegistryError("secret-field:" + path + "." + key)
            _reject_secret_names(child, path + "." + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_names(child, f"{path}[{index}]")


def _exact_fields(value, allowed, path):
    if not isinstance(value, dict):
        raise RegistryError("object-required:" + path)
    unknown = set(value) - allowed
    missing = allowed - set(value)
    if unknown:
        raise RegistryError("unknown-fields:" + path + ":" + ",".join(sorted(unknown)))
    if missing:
        raise RegistryError("missing-fields:" + path + ":" + ",".join(sorted(missing)))


def validate(registry):
    _reject_secret_names(registry)
    _exact_fields(registry, ROOT_FIELDS, "root")
    if registry["schema"] != 1:
        raise RegistryError("unsupported-schema")
    if not RFC3339_UTC.fullmatch(registry["updated_at"]):
        raise RegistryError("invalid-updated-at")
    profiles = registry["profiles"]
    if not isinstance(profiles, list) or not profiles:
        raise RegistryError("profiles-required")
    seen = set()
    guest_count = 0
    for index, profile in enumerate(profiles):
        path = f"profiles[{index}]"
        _exact_fields(profile, PROFILE_FIELDS, path)
        profile_id = profile["id"]
        if not isinstance(profile_id, str) or not ID.fullmatch(profile_id) or profile_id in seen:
            raise RegistryError("invalid-or-duplicate-profile-id:" + str(profile_id))
        seen.add(profile_id)
        if not isinstance(profile["display_name"], str) or not profile["display_name"].strip():
            raise RegistryError("display-name-required:" + profile_id)
        if profile["role"] not in ROLES:
            raise RegistryError("invalid-role:" + profile_id)
        mappings = profile["service_mappings"]
        if not isinstance(mappings, list):
            raise RegistryError("mapping-list-required:" + profile_id)
        for mapping_index, mapping in enumerate(mappings):
            _exact_fields(mapping, MAPPING_FIELDS, f"{path}.service_mappings[{mapping_index}]")
            if mapping["service"] not in SERVICES:
                raise RegistryError("unknown-service:" + str(mapping["service"]))
            if not SYNTHETIC_SUBJECT.fullmatch(mapping["opaque_subject_id"]):
                raise RegistryError("non-synthetic-subject:" + profile_id)
            if type(mapping["enabled"]) is not bool:
                raise RegistryError("mapping-enabled-must-be-boolean:" + profile_id)
        if not isinstance(profile["entitlements"], list) or (
            set(profile["entitlements"]) - ENTITLEMENTS
        ):
            raise RegistryError("invalid-entitlements:" + profile_id)
        preferences = profile["preferences"]
        if not isinstance(preferences, dict) or set(preferences) - PREFERENCES:
            raise RegistryError("invalid-preferences:" + profile_id)
        if profile["role"] == "guest":
            guest_count += 1
            if mappings:
                raise RegistryError("guest-service-mapping-denied")
            if set(profile["entitlements"]) & DENIED_GUEST:
                raise RegistryError("guest-private-entitlement-denied")
    if guest_count != 1 or "guest" not in seen:
        raise RegistryError("exactly-one-guest-required")
    if registry["active_profile_id"] not in seen:
        raise RegistryError("active-profile-missing")
    return copy.deepcopy(registry)


def restricted_guest_registry():
    return {
        "schema": 1,
        "active_profile_id": "guest",
        "profiles": [{
            "id": "guest",
            "display_name": "Guest",
            "role": "guest",
            "service_mappings": [],
            "entitlements": ["public_catalogue_browse", "clock", "local_settings_read"],
            "preferences": {"clock": "24h", "captions": False},
        }],
        "updated_at": "1970-01-01T00:00:00Z",
    }


def load(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return validate(data), "valid"
    except (OSError, json.JSONDecodeError, RegistryError, TypeError):
        return restricted_guest_registry(), "restricted-guest-fallback"


def activate(registry, profile_id, updated_at):
    candidate = copy.deepcopy(validate(registry))
    if profile_id not in {profile["id"] for profile in candidate["profiles"]}:
        raise RegistryError("profile-not-found:" + profile_id)
    candidate["active_profile_id"] = profile_id
    candidate["updated_at"] = updated_at
    return validate(candidate)


def sign_out(registry, updated_at):
    return activate(registry, "guest", updated_at)


def store(path, registry):
    destination = Path(path)
    encoded = (json.dumps(validate(registry), indent=2, sort_keys=True) + "\n").encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = destination.with_suffix(destination.suffix + ".previous")
    if destination.exists():
        current, status = load(destination)
        if status != "valid":
            raise RegistryError("refuse-to-back-up-invalid-current-registry")
        _atomic_write(previous, (json.dumps(current, indent=2, sort_keys=True) + "\n").encode())
    _atomic_write(destination, encoded)


def _atomic_write(path, payload):
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as target:
            target.write(payload)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
