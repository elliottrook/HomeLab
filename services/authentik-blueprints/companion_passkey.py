"""Pure validation of Authentik 2026.8's server-owned token-session login evidence.

Embedded in a provider-specific ScopeMapping; never consumes browser JSON.
"""
from datetime import datetime

PASSKEY_ACR = "urn:homelab:aster:webauthn:1"
COMPANION_FLOW_PATH = "/api/v3/flows/executor/aster-companion-passwordless/"


def companion_passkey_claims(provider, token, user, event, policy_epoch, now_epoch):
    """Return only an assurance claim; never change auth_time or disclose evidence."""
    if (getattr(provider, "pk", None) != 26
            or getattr(provider, "client_id", None) != "aster-companion"
            or getattr(token, "provider_id", None) != provider.pk
            or getattr(token, "actor", None) is not None
            or not getattr(user, "is_active", False)):
        return {}
    session = getattr(token, "session", None)
    if (session is None or getattr(session, "user_id", None) != user.pk
            or getattr(token, "user_id", None) != user.pk or event is None
            or getattr(event, "action", None) != "login"):
        return {}
    event_user = getattr(event, "user", None)
    context = getattr(event, "context", None)
    if (not isinstance(event_user, dict) or event_user.get("pk") != user.pk
            or not isinstance(context, dict) or context.get("is_user_switch")
            or context.get("auth_method") != "auth_mfa"):
        return {}
    http = context.get("http_request")
    args = context.get("auth_method_args")
    if (not isinstance(http, dict) or http.get("path") != COMPANION_FLOW_PATH
            or http.get("method") not in {"GET", "POST"} or not isinstance(args, dict)):
        return {}
    devices = args.get("mfa_devices")
    if (not isinstance(devices, list) or len(devices) != 1
            or not isinstance(devices[0], dict)
            or devices[0].get("app") != "authentik_stages_authenticator_webauthn"
            or devices[0].get("model_name") != "webauthndevice"):
        return {}
    created, authenticated = getattr(event, "created", None), getattr(token, "auth_time", None)
    if not isinstance(created, datetime) or not isinstance(authenticated, datetime):
        return {}
    if created.tzinfo is None or authenticated.tzinfo is None:
        return {}
    # Token issuance/refresh must stay bound to this exact authentication event.
    if (created != authenticated or created.timestamp() < policy_epoch
            or created.timestamp() > now_epoch):
        return {}
    return {"acr": PASSKEY_ACR}
