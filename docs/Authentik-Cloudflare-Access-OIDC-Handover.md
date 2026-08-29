# Authentik + Cloudflare Access OIDC Integration Handover

> Status: **Resolved — production working**
> Started: 2026-08-29 · Resolved: 2026-08-29 (via a separate ChatGPT troubleshooting session)
> Related: [Synology Drive Cloudflare Handover](Synology-Drive-Cloudflare-Handover.md)

## Goal

Protect the DSM/admin surface at `share.elliottrook.com` with Cloudflare
Access while keeping Synology Drive's public-share paths unauthenticated.
Cloudflare Access uses the existing Authentik OIDC provider, so the
administrator signs in with the normal Authentik password + passkey/MFA flow.
Cloudflare's built-in One-Time PIN is not used.

## Final production behavior

- `https://share.elliottrook.com/` → Cloudflare Access → Authentik → password
  + passkey/MFA → Synology DSM.
- `/d/*` → Cloudflare Access Bypass. Public Drive file-share link re-tested
  after cleanup and confirmed working without authentication.
- `/oo/*` → Cloudflare Access Bypass. Configuration retained; not re-tested at
  closeout because no suitable `/oo/` link was available at the time.
- Direct LAN DSM access remains the break-glass path:
  `https://192.168.20.41:5001`.
- Cloudflare OTP is not part of the design.

## Root cause

The OIDC failure was caused by **split DNS**. `auth.elliottrook.com` existed
only in internal DNS, resolving directly to Nginx Proxy Manager on the home
network. Cloudflare Access performs its authorization-code token exchange
from Cloudflare's own backend, not from the user's browser — and that backend
needed the Authentik token/JWKS/userinfo endpoints to be reachable through
Cloudflare's own authoritative DNS zone for the domain, which had no public
`auth.elliottrook.com` record. This produced the generic error seen
throughout troubleshooting: "Failed to fetch user/group information from the
identity provider."

The browser-side Authentik authorization flow always succeeded (confirmed
repeatedly during the original troubleshooting), which is what made this look
like a token/claims/signing-key/compatibility problem rather than a DNS one —
everything the browser touched worked fine; only the backend-to-backend leg
was broken.

## Resolution: publish Authentik through the existing Cloudflare Tunnel

Rather than expose NPM/Authentik directly via a WAN A record,
`auth.elliottrook.com` was added as another published application route on
the existing `synology-drive-share` Cloudflare Tunnel (the same tunnel used
for Drive sharing — see the Cloudflare handover doc).

Final route:
- Public hostname: `auth.elliottrook.com`
- Service: HTTPS
- Origin: `192.168.50.23` (Nginx Proxy Manager)
- TLS Origin Server Name: `auth.elliottrook.com`
- TLS verification: enabled, timeout 10s
- HTTP/2 connection: off
- Match SNI to Host: off

Traffic path:
`Cloudflare → Cloudflare Tunnel → NPM 192.168.50.23:443 → Authentik 192.168.50.22:9000`

Cloudflare created the public proxied DNS entry for this route automatically.
Public DNS was verified against `1.1.1.1`, and the Authentik OIDC discovery
endpoint returned HTTP 200 through the public tunnel path. Internal split DNS
continues resolving `auth.elliottrook.com` directly to NPM for LAN clients;
external/Cloudflare resolution now goes through the tunnel.

## Authentik OIDC configuration (unchanged from original setup)

- Provider: `Provider for Cloudflare Access`
- Application slug: `cloudflare-access`
- Client type: Confidential, Grant: Authorization Code
- Redirect URI: `https://delicate-glade-7e3a.cloudflareaccess.com/cdn-cgi/access/callback`
- Signing key: `authentik Self-signed Certificate`
- Scopes: `openid`, `email`, `profile`; "Include claims in ID token" enabled
- Issuer mode: per-provider/application slug
- Client secret: rotated during troubleshooting (see Security incident below)
  — not stored in this repository

Discovery endpoint:
`https://auth.elliottrook.com/application/o/cloudflare-access/.well-known/openid-configuration`

## Final Cloudflare Access application configuration

The broad DSM-protection application covers `share.elliottrook.com/*` with
policy `Jason - Full Access` (Allow; administrator email rule). Narrower
bypass applications cover `/d/*` and `/oo/*` as before.

Authentication settings on the broad application:
- Accept all available identity providers: **Off**
- Selected provider: **Authentik Production** (an OIDC provider object,
  renamed from `Authentik OIDC API Test` after validation — the same
  API-created object was kept through the rename, not recreated)
- Apply instant authentication: On
- Authenticate with Cloudflare One Client: Off

Two temporary/broken Authentik identity-provider entries created during
troubleshooting were deleted after production validation.

## Diagnostics that isolated the failure

Useful sequence, worth repeating in this order if this integration ever
regresses:

1. Authentik Events showed successful browser authorization and the correct
   Cloudflare callback (this was already known from the original
   troubleshooting above).
2. Cloudflare's standalone IdP test failed at the code-for-token exchange
   step specifically.
3. Authentik/NPM logs showed **no corresponding Cloudflare token POST**
   arriving during those failures — the request never arrived at all, which
   is the key clue pointing at a reachability problem rather than an
   application-level rejection.
4. A manual external POST to Authentik's token endpoint with deliberately
   invalid credentials returned `invalid_client` — proving the public HTTP
   POST path itself worked from an external test client.
5. A manual POST using real client credentials and a deliberately invalid
   authorization code returned `invalid_grant` — proving Authentik accepted
   the client credentials and reached authorization-code validation.
6. Cloudflare API inspection confirmed the saved OIDC URLs/scopes were
   correct.
7. Cloudflare account inspection identified the decisive discrepancy:
   `auth.elliottrook.com` was absent from Cloudflare's own authoritative DNS
   zone for the domain.
8. After publishing `auth.elliottrook.com` through the Cloudflare Tunnel,
   Cloudflare's OIDC test succeeded and returned the administrator email plus
   AMR values `pwd` and `mfa`.

## Secondary issue found during production cutover

After the backend reachability problem was fixed, the production Access
application still failed once because it had been assigned a similarly-named
but obsolete IdP object (`Authentik OIDC Test`) rather than the known-good
API-created provider. The callback `state` parameter exposed the IdP UUID,
which made the mismatch unambiguous. Selecting the correct provider fixed
production login; it was then renamed to `Authentik Production` for clarity.

A second UI trap: Cloudflare One Client authentication was accidentally
toggled on at one point and Cloudflare refused to save that state because no
account-level One Client session duration was configured. The intended,
final setting is **Off**.

## Security incident and cleanup

During API-based troubleshooting, a Cloudflare identity-provider create API
call returned the OIDC **client secret in its response**, and that response
was accidentally exposed within the troubleshooting conversation. The secret
was immediately treated as compromised and rotated in Authentik, then
Cloudflare was updated with the new secret. The old secret is invalid.

**Operational rule going forward:** never paste or record the full response
from an IdP-create API call — it may contain the client secret in plaintext.

Temporary, narrowly-scoped Cloudflare Access API tokens used during
troubleshooting were revoked after completion. Unrelated existing
DNS/certificate/tunnel tokens were left untouched. No client secret,
Cloudflare API token, tunnel credential, certificate credential, or other
secret is stored in this repository.

## Closeout validation

- Fresh private-browser login to bare `share.elliottrook.com` completed
  successfully through Authentik and reached DSM.
- Public `/d/*` Synology Drive share opened successfully in a private browser
  with no Cloudflare/Authentik authentication prompt.
- `/oo/*` bypass remains configured but was not re-tested at closeout (no
  suitable `/oo/` share link was available) — worth a quick confirmation next
  time an Office-format file is shared.
- Obsolete Authentik IdP objects were deleted; temporary Access API tokens
  were revoked.

## Final architecture

Cloudflare Access protects the administrative DSM surface, while narrow
path-based bypass applications preserve public Synology Drive sharing.
Authentik is the sole login method for the protected DSM application, and is
itself reachable externally only through the existing Cloudflare Tunnel to
NPM — never via direct WAN exposure. This returns the Synology Drive project
to its intended final architecture (Milestone 6, friend sharing).
