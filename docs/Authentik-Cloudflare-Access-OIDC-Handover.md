# Authentik + Cloudflare Access OIDC Integration Handover

> Status: **Resolved — production working**
> Started/Resolved: 2026-08-29
> Related: [Synology Drive Cloudflare Handover](Synology-Drive-Cloudflare-Handover.md)

## Goal

Protect the DSM/admin surface at `share.elliottrook.com` with Cloudflare Access while keeping Synology Drive public-share paths unauthenticated. Cloudflare Access uses the existing Authentik OIDC provider, so the administrator signs in with the normal Authentik password + passkey/MFA flow. Cloudflare One-Time PIN is not used.

## Final production behavior

- `https://share.elliottrook.com/` -> Cloudflare Access -> Authentik -> password + passkey/MFA -> Synology DSM.
- `/d/*` -> Cloudflare Access Bypass. Public Drive file-share link re-tested after cleanup and confirmed working without authentication.
- `/oo/*` -> Cloudflare Access Bypass. Configuration retained; not re-tested at closeout because no suitable `/oo/` link was available.
- Direct LAN DSM access remains the break-glass path: `https://192.168.20.41:5001`.
- Cloudflare OTP is not part of the design.

## Final Cloudflare Access application

The broad DSM protection application covers `share.elliottrook.com/*` with policy `Jason - Full Access` (Allow; administrator email rule). More-specific bypass applications cover `/d/*` and `/oo/*`.

Authentication settings on the broad application:

- Accept all available identity providers: **Off**
- Selected provider: **Authentik Production - oidc**
- Apply instant authentication: **On**
- Authenticate with Cloudflare One Client: **Off**

The two temporary/broken Authentik identity-provider entries were removed after production validation. The working API-created provider was renamed from `Authentik OIDC API Test` to `Authentik Production` and the application retained the same IdP object through the rename.

## Root cause

The principal OIDC failure was caused by split DNS.

`auth.elliottrook.com` existed only in internal DNS, where clients resolved it directly to Nginx Proxy Manager. Cloudflare Access performs the authorization-code token exchange from Cloudflare's own backend, not from the user's browser. Cloudflare's backend therefore needed public DNS/public reachability for the Authentik token/JWKS/userinfo endpoints. Because the authoritative Cloudflare DNS zone had no public `auth.elliottrook.com` record (and no suitable wildcard), the Cloudflare backend could not resolve/reach Authentik. This produced Cloudflare's generic error:

> Authentication error — Failed to fetch user/group information from the identity provider.

The browser-side Authentik authorization flow still succeeded, which initially made the problem look like a token, claim, signing-key, or Authentik compatibility problem.

## Resolution: publish Authentik through the existing Cloudflare Tunnel

Rather than expose NPM/Authentik directly through a WAN A record, `auth.elliottrook.com` was added as another published application route on the existing `synology-drive-share` Cloudflare Tunnel.

Final route:

- Public hostname: `auth.elliottrook.com`
- Service: HTTPS
- Origin: `192.168.50.23` (Nginx Proxy Manager)
- TLS Origin Server Name: `auth.elliottrook.com`
- TLS verification: enabled
- TLS timeout: 10 seconds
- HTTP/2 connection: off
- Match SNI to Host: off

Traffic path:

`Cloudflare -> Cloudflare Tunnel -> NPM 192.168.50.23:443 -> Authentik 192.168.50.22:9000`

Cloudflare created the public proxied DNS entry for the tunnel route. Public DNS was verified against `1.1.1.1`, and the Authentik OIDC discovery endpoint returned HTTP 200 through the public tunnel path.

Internal split DNS can continue resolving `auth.elliottrook.com` directly to NPM at `192.168.50.23`; external/Cloudflare resolution uses the tunnel.

## Authentik OIDC configuration

Authentik application/provider remains the Cloudflare Access OAuth2/OpenID Connect integration:

- Provider: `Provider for Cloudflare Access`
- Application slug: `cloudflare-access`
- Client type: Confidential
- Grant: Authorization Code
- Redirect URI: `https://delicate-glade-7e3a.cloudflareaccess.com/cdn-cgi/access/callback`
- Signing key: `authentik Self-signed Certificate`
- Scopes: `openid`, `email`, `profile`
- Include claims in ID token: enabled
- Issuer mode: per-provider/application slug
- Client secret: **not stored in this repository**

Discovery endpoint:

`https://auth.elliottrook.com/application/o/cloudflare-access/.well-known/openid-configuration`

Cloudflare generic OIDC endpoints use Authentik's authorization, token, userinfo and provider-specific JWKS endpoints. No secret values are recorded here.

## Diagnostics that isolated the failure

The following tests were useful and should be repeated in this order if this integration ever regresses:

1. Authentik Events showed successful browser authorization and the correct Cloudflare callback.
2. Cloudflare's standalone IdP test originally failed at code-for-token exchange.
3. Authentik/NPM logs showed no corresponding Cloudflare token POST during those failures.
4. An external manual POST to Authentik's token endpoint returned `invalid_client` with deliberately invalid credentials, proving the public HTTP POST path itself worked from the test client.
5. A manual POST using the actual client credentials and a deliberately invalid authorization code returned `invalid_grant`, proving Authentik accepted the client credentials and reached authorization-code validation.
6. Cloudflare API inspection confirmed the saved OIDC URLs/scopes were correct.
7. Cloudflare account inspection identified the decisive discrepancy: `auth.elliottrook.com` was absent from public authoritative DNS.
8. After publishing `auth.elliottrook.com` through the Cloudflare Tunnel, Cloudflare's OIDC Test succeeded and returned the administrator email plus AMR values `pwd` and `mfa`.

## Secondary issue discovered during production cutover

After the OIDC backend problem was fixed, the production Access application still failed once because it had accidentally been assigned the similarly named obsolete IdP `Authentik OIDC Test`, rather than the known-good API-created provider.

The callback `state` exposed the IdP UUID and made the mismatch unambiguous. Selecting the known-good provider fixed production login. It was then renamed to `Authentik Production`.

A second UI trap occurred when Cloudflare One Client authentication was inadvertently toggled on. Cloudflare refused to save that state because no account-level One Client authentication session duration was configured. The intended setting is **Off**; no One Client session duration was added.

## Security incident and cleanup

During API troubleshooting, Cloudflare's identity-provider create API returned the OIDC `client_secret` in its response and that response was accidentally exposed in the troubleshooting conversation. The secret was immediately treated as compromised and rotated in Authentik. Cloudflare was then updated with the new secret. The old secret is invalid.

Operational rule: **never paste or record the full response from an IdP-create API call; it may contain the client secret in plaintext.**

Temporary narrow Cloudflare Access API tokens used during troubleshooting were revoked after completion. Existing unrelated DNS/certificate/tunnel tokens were left untouched.

No client secret, Cloudflare API token, tunnel credential, certificate credential, or other secret is stored in this repository.

## Closeout validation

Production was validated after cleanup:

- Renamed `Authentik Production` provider remained attached to the Access application.
- Fresh private-browser login to bare `share.elliottrook.com` completed successfully through Authentik and reached DSM.
- Public `/d/*` Synology Drive share opened successfully in a private browser without Cloudflare/Authentik authentication.
- `/oo/*` bypass remains configured but was not re-tested during closeout because no `/oo/` share link was available.
- Obsolete Authentik IdPs were deleted.
- Temporary Access API tokens were revoked.

## Final architecture decision

Cloudflare Access protects the administrative DSM surface, while narrow path-based bypass applications preserve public Synology Drive sharing. Authentik remains the sole login method for the protected DSM application and supplies password + passkey/MFA authentication. Authentik itself is externally reachable only through the existing Cloudflare Tunnel to NPM, avoiding direct WAN exposure.

This resolves the Authentik + Cloudflare Access OIDC handover and returns the Synology Drive project to its intended final architecture.
