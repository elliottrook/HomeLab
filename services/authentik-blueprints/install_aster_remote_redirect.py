"""Checkpoint, install or roll back Aster Remote's strict OIDC redirect.

Run inside Authentik's ``ak shell``.  The checkpoint contains only redirect
metadata; it never contains a client secret, token, session or user record.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from django.db import transaction
from authentik.providers.oauth2.models import (
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RedirectURIType,
)


PROVIDER_PK = 26
PROVIDER_NAME = "Aster Companion"
CLIENT_ID = "aster-companion"
REMOTE = "https://aster.elliottrook.com/remote/"
EXPECTED = {
    "aster-companion://callback",
    "https://aster.elliottrook.com/companion",
}
CHECKPOINT = Path("/data/aster-checkpoints/aster-remote-redirect.json")


def rows(provider):
    return [
        {
            "matching_mode": str(item.matching_mode),
            "url": item.url,
            "redirect_uri_type": str(item.redirect_uri_type),
        }
        for item in provider.redirect_uris
    ]


def provider():
    item = OAuth2Provider.objects.get(pk=PROVIDER_PK)
    if (
        item.name != PROVIDER_NAME
        or item.client_id != CLIENT_ID
        or str(item.client_type) != "public"
        or item.authentication_flow.slug != "aster-companion-reauthentication"
    ):
        raise RuntimeError("unexpected-provider-boundary")
    return item


def checkpoint(item):
    current = rows(item)
    urls = {row["url"] for row in current}
    if REMOTE in urls:
        raise RuntimeError("remote-redirect-already-present")
    if urls != EXPECTED or len(current) != len(EXPECTED):
        raise RuntimeError("unexpected-redirect-boundary")
    if CHECKPOINT.exists():
        saved = json.loads(CHECKPOINT.read_text())
        if saved.get("redirect_uris") != current:
            raise RuntimeError("checkpoint-current-mismatch")
        return
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps({
        "schema": 1,
        "provider_pk": PROVIDER_PK,
        "client_id": CLIENT_ID,
        "redirect_uris": current,
    }, indent=2, sort_keys=True) + "\n")
    os.chmod(CHECKPOINT, 0o600)


def decode(saved):
    if (
        saved.get("schema") != 1
        or saved.get("provider_pk") != PROVIDER_PK
        or saved.get("client_id") != CLIENT_ID
    ):
        raise RuntimeError("checkpoint-boundary")
    return [
        RedirectURI(
            matching_mode=RedirectURIMatchingMode(row["matching_mode"]),
            url=row["url"],
            redirect_uri_type=RedirectURIType(row["redirect_uri_type"]),
        )
        for row in saved["redirect_uris"]
    ]


def install():
    with transaction.atomic():
        item = provider()
        checkpoint(item)
        updated = list(item.redirect_uris) + [RedirectURI(
            matching_mode=RedirectURIMatchingMode.STRICT,
            url=REMOTE,
            redirect_uri_type=RedirectURIType.AUTHORIZATION,
        )]
        item.redirect_uris = updated
        # redirect_uris is Authentik's serialized property rather than a
        # concrete Django field, so the normal model save path is required.
        item.save()
        if {row["url"] for row in rows(item)} != EXPECTED | {REMOTE}:
            raise RuntimeError("redirect-install-validation")
    print(json.dumps({"outcome": "installed", "provider": CLIENT_ID,
                      "redirect_count": 3}, sort_keys=True))


def rollback():
    saved = json.loads(CHECKPOINT.read_text())
    with transaction.atomic():
        item = provider()
        if {row["url"] for row in rows(item)} != EXPECTED | {REMOTE}:
            raise RuntimeError("rollback-current-mismatch")
        item.redirect_uris = decode(saved)
        item.save()
        if rows(item) != saved["redirect_uris"]:
            raise RuntimeError("redirect-rollback-validation")
    print(json.dumps({"outcome": "rolled-back", "provider": CLIENT_ID,
                      "redirect_count": 2}, sort_keys=True))


def verify():
    item = provider()
    current = rows(item)
    urls = {row["url"] for row in current}
    expected = EXPECTED | ({REMOTE} if REMOTE in urls else set())
    if urls != expected or len(current) != len(expected):
        raise RuntimeError("redirect-verify-boundary")
    print(json.dumps({"outcome": "verified", "provider": CLIENT_ID,
                      "redirect_count": len(current),
                      "remote_present": REMOTE in urls}, sort_keys=True))


action = os.environ.get("ASTER_REMOTE_REDIRECT_ACTION")
if action == "install":
    install()
elif action == "rollback":
    rollback()
elif action == "verify":
    verify()
else:
    raise RuntimeError("ASTER_REMOTE_REDIRECT_ACTION must be install, rollback or verify")
