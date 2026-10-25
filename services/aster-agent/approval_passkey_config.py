"""Fail-closed configuration for independent approval passkey assurance."""

from __future__ import annotations

PASSKEY_ACR = "urn:homelab:aster:webauthn:1"


def passkey_acrs(raw: str | None) -> frozenset[str]:
    """Return the one reviewed ACR, or an empty Yellow-only mapping.

    Generic MFA, alternate assurance labels and multi-value configuration are
    rejected instead of being silently ignored or promoted.
    """
    value = (raw or "").strip()
    if not value:
        return frozenset()
    if value != PASSKEY_ACR:
        raise ValueError(
            "ASTER_APPROVAL_PASSKEY_ACRS must be the exact reviewed Aster WebAuthn ACR"
        )
    return frozenset({PASSKEY_ACR})
