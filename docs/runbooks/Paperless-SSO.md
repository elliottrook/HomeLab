# Paperless passkey SSO

Use https://paperless.elliottrook.com. Native OIDC redirects to Authentik and
links its immutable subject to the existing `jason` account. No separate
Paperless password is needed. A fresh Authentik session uses the dedicated
`paperless-passkey` flow (WebAuthn validation, then user login); existing sessions
can complete SSO immediately. Other applications retain their own flows.

## Configuration authority

- Authentik application `paperless`, OAuth2 provider 37 `Paperless OIDC`, bound
  only to Jason. Confidential authorization-code client; PKCE S256; default
  openid/profile/email mappings. Strict callback:
  `https://paperless.elliottrook.com/accounts/oidc/authentik/login/callback/`.
- Discovery: `https://auth.elliottrook.com/application/o/paperless/.well-known/openid-configuration`.
- Passkey validation: `webauthn` only, user verification required, missing
  authenticator denied; followed by user login. No password stage.
- Paperless Compose environment at `/opt/paperless-ngx/docker-compose.env`:
  `PAPERLESS_APPS=allauth.socialaccount.providers.openid_connect`,
  `PAPERLESS_DISABLE_REGULAR_LOGIN=true`, `PAPERLESS_REDIRECT_LOGIN_TO_SSO=true`,
  `PAPERLESS_SOCIALACCOUNT_ALLOW_SIGNUPS=false`, `PAPERLESS_SOCIAL_AUTO_SIGNUP=false`.
  Provider JSON includes `OAUTH_PKCE_ENABLED=true`, provider_id `authentik`,
  discovery URL and protected client credentials. Never export raw environment.
- Logout URL: `https://auth.elliottrook.com/application/o/paperless/end-session/`.
- NPM host25 retains source restrictions and strips caller identity headers;
  Paperless authenticates OIDC itself. `enable_oidc_proxy.mjs` records cutover.
- OPNsense rule sequence2682 allows only Paperless .70.15 to NPM .50.23 TCP443.

## Verification

A signed-out browser should reach Authentik without a Paperless password form.
After the owner completes the passkey challenge it must open the existing
Paperless account. Do not create a second account if linking fails. Check
SocialAccount provider `authentik` against the provider's hashed user subject.
Anonymous and forged-header `/api/documents/` requests must return401.
Run `/opt/paperless-summary/check_summary.py` on LXC115; all health checks pass.

## Recovery

Checkpoints from 2026-09-23 are root-only on their respective hosts:

- LXC115: `/root/paperless-env-before-sso-20260923` and
  `/root/paperless-db-before-sso-20260923.sqlite3`.
- LXC107: `/root/npm-before-paperless-sso-20260923.sqlite`.
- OPNsense: `/conf/backup/config-paperless-before-oidc-20260923.xml`.

For local administrative recovery, use an authenticated SSH session to LXC115
and Paperless's management commands. Local web-login disablement does not revoke
existing API tokens or disable Django administrative recovery. Keep the bootstrap
credential local; routine users should never need it.

If SSO must be rolled back, restore only the prior Paperless environment, recreate
only the webserver, reattach Authentik application `paperless` to retained provider
34, reattach provider34 to the embedded outpost, and restore only host25's
previous NPM advanced configuration through NPM.
Remove only rule2682 if it is no longer needed. Preserve unrelated changes and
new documents; do not overwrite entire live databases or firewall configuration
from checkpoints. The pre-linked SocialAccount can remain inert during rollback.

Service-only offsite backup excludes OIDC secrets, database and documents.
Full guest recovery is local/TrueNAS only.

References: [Authentik integration](https://integrations.goauthentik.io/documentation/paperless-ngx/),
[passwordless flows](https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_validate/#passwordless-authentication).
