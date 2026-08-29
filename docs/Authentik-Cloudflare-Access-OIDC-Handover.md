# Authentik + Cloudflare Access OIDC Integration Handover

> Status: Blocked — authentication error after successful Authentik login
> Started: 2026-08-29
> Related: [Synology Drive Cloudflare Handover](Synology-Drive-Cloudflare-Handover.md)

## Goal

Protect the DSM login surface exposed via `share.elliottrook.com` (see the
Cloudflare handover doc above) with Cloudflare Access, using the household's
existing Authentik SSO as the identity provider — rather than a separate login
method — so this login stays consistent with the passkey/WebAuthn flow already
used for other Authentik-protected services.

Cloudflare Access itself is correctly configured and confirmed working
independent of this problem: visiting the bare hostname (no path) correctly
triggers a Cloudflare Access login challenge, while Drive share link paths
bypass it entirely (see "Cloudflare Access application setup" below). The
remaining problem is specifically about using Authentik as the login method.

## The error

After clicking "Authentik" on the Cloudflare Access login screen and
completing a normal password + passkey login, Cloudflare returns:

> **Authentication error**
> Failed to fetch user/group information from the identity provider. Please
> contact your Access administrator if this continues.

Authentik's own Events log shows the browser-side authorization step
completing successfully — user `jason` (`jason@yampy.ca`) authenticated, the
`authorize_application` event was logged for the "Cloudflare Access"
application with the correct `redirect_uri`
(`https://delicate-glade-7e3a.cloudflareaccess.com/cdn-cgi/access/callback`),
correct `scope=openid email profile`, and `response_type=code`. No further
Events log entries appear after that — but this may not mean anything, since
Authentik's Events UI mainly logs user-facing flow actions, not necessarily
every server-to-server API call (token exchange, userinfo).

**Conclusion so far:** the browser-side OAuth authorization step works
perfectly. The failure happens in the subsequent server-to-server exchange
between Cloudflare's backend and Authentik (token exchange and/or userinfo
call), which neither side's currently-available logs show us directly.

## Cloudflare Zero Trust account details

- Team name: `delicate-glade-7e3a`
- Team domain: `delicate-glade-7e3a.cloudflareaccess.com`
- Account login: an Apple private-relay email (shown in dashboard top-left)

## Cloudflare Access application setup (already working, not part of the problem)

Three Applications exist under **Access → Applications**, all on the
`share.elliottrook.com` hostname:

| Application | Path | Policy | Action |
|---|---|---|---|
| DSM login protection (renamed to include "Allow") | `/*` | Jason - Full Access (Include: Emails = `jason@yampy.ca`) | Allow |
| Drive Share Links Bypass - /d/ | `/d/*` | Bypass Authentication just for link share (Include: Everyone) | Bypass |
| Drive Share Links Bypass - /oo/* | `/oo/*` | same Bypass policy as above | Bypass |

This three-way split was necessary because Synology Drive's public sharing
uses URL paths `/d/f/`, `/d/s/`, `/d/r/` (simple/public/file-request shares)
and `/oo/r/`, `/oo/t/` (Synology Office document shares) — confirmed by
reading the NAS's own nginx config
(`/usr/local/etc/nginx/conf.d/dsm.syno-app-portal.SynologyDrive.conf`).
Cloudflare evaluates Bypass policies first / most-specific-path-wins, so these
two narrow Bypass applications correctly override the broad `/*` login
requirement for just the share-link paths.

**This routing is confirmed working**: visiting `https://share.elliottrook.com`
directly correctly triggers the Access login challenge.

## Authentik OIDC provider configuration (the part that isn't working)

**Provider** (`Applications → Providers`, type OAuth2/OpenID Provider):

- Name: `Provider for Cloudflare Access`
- Authorization Flow: `default-provider-authorization-explicit-consent`
- Client Type: Confidential
- Client ID: `s6XvSZ8BvvTCb8TI4LYaf23HatsiYhpd6jzTQmx2`
- Client Secret: set (not recorded here — retrieve fresh from the provider
  page if needed)
- Grant Types: Authorization Code only
- Redirect URIs/Origins: four "Strict / Authorization" entries, all appearing
  to point to `https://delicate-glade-7e3a.cloudflareaccess.com/cdn-cgi/access/callback`
  — **these look like duplicates and haven't been de-duplicated or verified
  byte-for-byte identical; worth checking first**, in case one has a subtle
  difference (trailing slash, etc.) that matters at the token-exchange step
  even though it didn't block the authorize step.
- Signing Key: `authentik Self-signed Certificate` (confirmed set — ruling out
  the most commonly cited cause of this exact Cloudflare error, see Research
  below)
- Scopes (Property Mappings, both in the main scope-mapping section and under
  Advanced protocol settings): `authentik default OAuth Mapping: OpenID
  'email'`, `'openid'`, `'profile'` — 3 items selected, confirmed correctly
  attached to the Provider (not just requested by the client)
- Encryption Key: none (JWE not in use)
- Subject Mode: Based on the User's hashed ID
- Include claims in id_token: **On** — meaning the ID token itself should
  already carry email/profile claims directly, without strictly requiring a
  separate userinfo call
- Issuer mode: Each provider has a different issuer, based on the application
  slug

**Application** (`Applications → Applications`): linked to the provider
above, slug `cloudflare-access`.

**OIDC discovery confirmed working** — fetched directly and returned valid
data:
```
https://auth.elliottrook.com/application/o/cloudflare-access/.well-known/openid-configuration
```
Key endpoints from that document:
- `issuer`: `https://auth.elliottrook.com/application/o/cloudflare-access/`
- `authorization_endpoint`: `https://auth.elliottrook.com/application/o/authorize/`
- `token_endpoint`: `https://auth.elliottrook.com/application/o/token/`
- `userinfo_endpoint`: `https://auth.elliottrook.com/application/o/userinfo/`
- `jwks_uri`: `https://auth.elliottrook.com/application/o/cloudflare-access/jwks/`
- `scopes_supported`: `email`, `profile`, `openid`
- `claims_supported` includes `email`, `email_verified`, `name`, `groups`,
  etc.

## Cloudflare-side OpenID Connect login method configuration

Under **Settings → Authentication → Login methods → Authentik** (OpenID
Connect type):

- App ID: the Authentik Client ID above
- Client secret: the Authentik Client Secret above
- Auth URL: `https://auth.elliottrook.com/application/o/authorize/`
- Token URL: `https://auth.elliottrook.com/application/o/token/`
- Certificate URL: `https://auth.elliottrook.com/application/o/cloudflare-access/jwks/`
- Email claim: `email`
- PKCE: Off
- Enable SCIM: Off
- OIDC Scopes: `openid`, `email`, `profile` (Cloudflare's required minimum)
- No custom OIDC Claims added

## Diagnostics already performed

1. **External reachability check** (via direct HTTP requests from outside the
   home network, simulating what Cloudflare's backend needs to do):
   - `GET https://auth.elliottrook.com/application/o/userinfo/` → `401
     Unauthorized` (correct/expected for an unauthenticated request — proves
     the endpoint is reachable and responding normally, not blocked by a
     firewall/reverse-proxy issue)
   - `GET https://auth.elliottrook.com/application/o/token/` → `405 Method Not
     Allowed` (correct/expected since it requires POST — same conclusion,
     endpoint is reachable)
   - **Conclusion: this rules out basic network/reverse-proxy connectivity
     problems as the cause.**

2. **Researched the exact Cloudflare error message.** Found it is a known,
   previously-reported issue specifically with Authentik + Cloudflare Access
   OIDC integrations:
   - https://github.com/goauthentik/authentik/issues/3422
   - https://github.com/goauthentik/authentik/issues/7526
   - https://community.cloudflare.com/t/failed-to-fetch-user-group-information-from-the-identity-provider/557551
   - One commonly cited cause in that research: a missing Signing Key on the
     Authentik provider. **Checked and ruled out** — the Signing Key is
     correctly set.

3. **Reviewed every visible Authentik provider setting** (see configuration
   list above) — scope mappings, grant types, redirect URIs, signing key,
   issuer mode, "include claims in id_token" — nothing else looked obviously
   wrong.

## Hypotheses not yet ruled out / suggested next steps

1. **The four duplicate-looking redirect URI entries** on the Authentik
   provider — worth deleting down to a single, verified-exact entry matching
   Cloudflare's callback URL, in case one has a subtle mismatch that only
   matters at the token-exchange step (which uses the same `redirect_uri`
   parameter again, per OAuth2 spec) rather than the authorize step.

2. **A `groups` claim may be expected by Cloudflare but never configured on
   the Authentik side.** The error text specifically says "user/**group**
   information." Authentik's `claims_supported` list does include `groups`,
   but no explicit scope/mapping for it was added to the Provider's scope
   list (only `email`/`openid`/`profile` were selected). Worth trying: add a
   `groups` scope mapping to the Provider and see if the error changes or
   resolves.

3. **Authentik's raw server/application logs have not been checked** — only
   the Events UI was reviewed, which may not surface every API-level request.
   If SSH/log access to the Authentik host is available, checking its actual
   web server or application logs around the time of a login attempt (for
   requests to `/application/o/token/` or `/application/o/userinfo/` from
   Cloudflare's backend IP ranges) would show the literal HTTP status/error
   Authentik returned to Cloudflare, which would likely resolve this quickly.

4. **This may be a genuine Cloudflare-side quirk specific to Authentik's OIDC
   responses** (the linked GitHub issues suggest this is a recurring
   pain point for multiple people, not unique to this setup) — may be worth
   asking in Cloudflare's community forum or Authentik's GitHub issues with
   the specific configuration details above, since others may have found a
   fix not surfaced in the initial research.

## Current state (not yet a working fallback)

As of this handover, Authentik was left as the only realistic login option
tested against the DSM-protection Application, and it fails with the error
above. The originally-offered "Sign in with: Cloudflare" (Cloudflare account
OAuth) option was also tried earlier and rejected, because it authenticates
using a different email than the policy's required `jason@yampy.ca`.
**Practically, this means the Cloudflare Access path to DSM is not currently
usable by anyone until this is fixed** — though this only affects the
Cloudflare Tunnel path; direct LAN access to DSM
(`https://192.168.20.41:5001`) is completely unaffected and still works
normally.

**Recommended immediate fallback, not yet applied:** enable Cloudflare's
built-in **One-Time PIN** login method (Settings → Authentication → Login
methods → Add → One-time PIN — zero extra configuration needed) and make sure
it's available on the DSM-protection Application's Authentication tab. That
restores working remote access via email verification while the Authentik
integration above gets debugged separately. Swapping back to Authentik once
fixed just means re-confirming it's still enabled as an identity provider
there — it doesn't require redoing any of the Access/Bypass routing, which is
unrelated and already confirmed correct.
