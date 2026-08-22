# Service Authorization Onboarding

## Purpose

This runbook is the repeatable process for adding HomeLab services to
Authentik without redesigning the integration each time. Complete one service
at a time, keep its direct-management address available until validation is
finished, and record the result in the table at the end of this document.

There is no safe one-click conversion for every service. The quickest reliable
approach is to standardize on two patterns:

1. **Native OIDC/OAuth2** when the application supports it. This is the preferred
   path because Authentik becomes the application login and there is usually no
   second password.
2. **Forward auth** when the application has no suitable native SSO. This adds
   an Authentik gate but normally leaves the application's own login enabled.

Do not place network control-plane protocols, SSH, DNS, storage protocols,
camera streams or the Tailscale control path behind an HTTP authentication
proxy. This runbook applies only to browser-based web interfaces.

## Service plan

The exact capabilities can vary by installed version and licence. Confirm the
application's current authentication settings before selecting a path.

| Service | Recommended path | Suggested name | Important note |
|---|---|---|---|
| Nginx Proxy Manager | Forward auth | `proxy.elliottrook.com` | Complete and tested; NPM login remains |
| Homepage | Forward auth | `home.elliottrook.com` | Keep health/widget requests in mind |
| Pi-hole #1 and #2 web UIs | Forward auth | `dns1.elliottrook.com`, `dns2.elliottrook.com` | DNS on TCP/UDP 53 is never proxied |
| Frigate | Native OIDC if available; otherwise forward auth | `frigate.elliottrook.com` | RTSP, ONVIF and recordings remain direct |
| Portainer | Native OAuth/OIDC if supported by the installed edition; otherwise forward auth | `portainer.elliottrook.com` | Keep a local break-glass administrator |
| Proxmox web UI | Native OpenID Connect realm | `proxmox.elliottrook.com` | Keep the local `root@pam` recovery path |
| TrueNAS web UI | Native OIDC if supported by the installed release; otherwise forward auth | `truenas.elliottrook.com` | SMB, NFS and iSCSI are not proxied |
| Synology web UIs | Native SSO/OIDC if supported; otherwise forward auth | `nas.elliottrook.com`, `backup-nas.elliottrook.com` | SMB and backup traffic remain direct |
| UniFi OS/Network web UI | Forward auth | `unifi.elliottrook.com` | Preserve local console and direct URL |
| OPNsense web UI | Keep LAN/Tailscale-only initially | `firewall.elliottrook.com` only if later approved | Avoid making proxy/auth failure block firewall recovery |
| Tailscale | No Authentik proxy | Existing tailnet | It is already the private access layer |
| SSH endpoints | No Authentik proxy | Existing addresses | Continue using SSH keys through LAN/Tailscale |
| Reolink camera UI | No general proxy | Existing camera address | Keep isolated; use Frigate as the normal interface |
| Home Assistant | Retain native authentication unless a reviewed OIDC integration supports every client | `homeassistant.elliottrook.com` | Test mobile app, callbacks and emergency access |
| Beszel | Native OIDC if supported by the installed version; otherwise forward auth | `metrics.elliottrook.com` | Keep agents on their private direct path |
| Jellyfin | Native SSO only with a supported integration; otherwise forward auth | `jellyfin.elliottrook.com` | Test TV and mobile clients before enforcing |
| Plex | Retain Plex authentication; optionally add forward auth for browser-only administration | `plex.elliottrook.com` | Do not break TV, mobile or remote clients |
| Seerr | Native OIDC if supported by the installed version; otherwise forward auth | `requests.elliottrook.com` | Test Plex/Jellyfin callbacks |
| Calibre/Audiobookshelf | Native OIDC where supported; otherwise forward auth | Service-specific names | Test mobile readers and players |
| Media-automation applications | Forward auth for browser UIs only | Service-specific names | Preserve API keys and private inter-service routes |
| Hermes web UI | Keep Lab/Tailscale-only initially | Lab address | Do not proxy its provider/API path |
| Ollama API | No Authentik proxy | `192.168.70.11:11434` | Non-browser model API; keep isolated by firewall |
| Future Forgejo | Native OIDC | `git.elliottrook.com` | Preferred native-SSO pattern |
| Immich | Native OIDC if supported by deployed version | `photos.elliottrook.com` | Validate mobile-client behaviour |
| Future Paperless-ngx | Native OIDC if supported by deployed version | `paperless.elliottrook.com` | Preserve API/automation access |

Start with ordinary applications. Leave OPNsense, Proxmox, storage appliances
and other recovery-critical interfaces until the pattern has been proven on
several lower-risk services.

## Information worksheet

Fill this out before changing anything:

```text
Service:
Public/internal hostname:
Backend scheme, address and port:
Authentication path: native OIDC / forward auth / no proxy
Application version and edition:
Direct fallback URL:
Backup completed:
Authentik group allowed:
API, mobile or non-browser clients that may be affected:
Rollback owner and method:
```

Use a dedicated Authentik group such as `homelab-admins` for administrative
interfaces. Create narrower groups later where another user should have access
to media, photos, documents or home automation without receiving access to the
infrastructure control plane.

## Common preparation for either path

1. Confirm the service works at its current direct URL and that its existing
   credentials work in a private browser window.
2. Back up the application and NPM configuration using the relevant runbook.
3. Confirm a local console or direct fallback remains available if Authentik,
   DNS, TLS or NPM fails.
4. Choose a unique hostname under `elliottrook.com`.
5. Create the NPM proxy host with the correct backend scheme, address and port.
6. Attach the existing wildcard certificate, enable Force SSL and leave public
   WAN exposure disabled. These names resolve privately to `192.168.50.23`.
7. Add the hostname to OPNsense and both Pi-holes. Confirm every resolver
   returns `192.168.50.23` before testing the browser.
8. Verify the new HTTPS name reaches the application before enabling Authentik.

For services that use WebSockets, streaming, large uploads or long-running
requests, enable and test the corresponding NPM features before adding the
authentication layer.

## Path A — native OIDC/OAuth2

Use this path whenever the installed application has a supported OIDC or OAuth2
client. Field labels vary, but the values follow the same pattern.

### In Authentik

1. Go to **Applications > Providers** and create an **OAuth2/OpenID Provider**.
2. Give it a service-specific name; do not reuse one client secret across
   applications.
3. Select an authorization flow and the normal invalidation/logout flow.
4. Use the application's exact HTTPS callback/redirect URI. Copy it from the
   application documentation or its SSO settings; do not guess the path.
5. Use confidential-client authentication when supported and generate a strong
   client secret.
6. Include at least the `openid`, `profile` and `email` scopes. Add groups only
   when the application actually uses them.
7. Create an Authentik application bound to the provider.
8. Bind an access policy or group so authorization is explicit rather than open
   to every Authentik user.
9. Copy the client ID, client secret and issuer/discovery URL directly into the
   target application's SSO settings. Store the secret in the protected vault,
   never in this repository.

### In the application

1. Keep the existing local administrator enabled as a break-glass account.
2. Enter the Authentik issuer/discovery URL, client ID, client secret and exact
   redirect URI.
3. Map a stable claim for the username, normally `preferred_username` or email
   according to the application's documented requirement.
4. Map groups or administrator roles only after a normal-user login succeeds.
5. Leave automatic account creation disabled unless it is intentionally needed.
6. Save, but do not disable the application's password login yet.

### Validate native SSO

1. Use a fresh private browser window.
2. Open the service hostname and choose its OIDC/SSO login.
3. Complete Authentik password and passkey authentication.
4. Confirm the correct local account and privilege level were selected.
5. Test sign-out, sign-in again, an expired session and denied access using a
   user outside the allowed group.
6. Test any mobile client, API token, webhook or automation separately.
7. Confirm the local break-glass login still works from the direct URL.

Only after all tests pass should SSO become the default login. Retain at least
one tested local recovery account unless the application's recovery design
explicitly provides another independent path.

## Path B — Authentik forward auth

Use this for a browser interface without dependable native OIDC. The service's
existing login normally remains, producing:

```text
Service URL -> Authentik password + passkey -> application login -> service
```

### In Authentik

1. Go to **Applications > Providers** and create a **Proxy Provider**.
2. Select forward-auth mode. Prefer one provider/application per service while
   building the system because this gives independent policy and rollback.
3. Set the external host to the service's final HTTPS hostname.
4. Create the Authentik application and bind it to the provider.
5. Bind the intended group or policy.
6. Add the provider/application to the embedded outpost.
7. Confirm the embedded outpost still uses:

   ```text
   authentik_host = https://auth.elliottrook.com
   ```

### In NPM

1. Start from the tested minimal forward-auth configuration used by proxy host
   #2; change only the target service and generated Authentik values.
2. Preserve `Host`, `X-Forwarded-Proto`, `X-Forwarded-For` and the original URL.
3. Do not send `X-authentik-*` identity headers unless the target application is
   explicitly configured to consume them.
4. Because this NPM release hides the Advanced field, use the backup-first
   database/API regeneration procedure in [Authorization](08-Authorization.md).
   Update only the new proxy host's ID—never assume it is host #2.
5. Run `nginx -t`, inspect the generated host file and reload NPM if required.

### Validate forward auth

1. Confirm an unauthenticated request receives a `302` into
   `/outpost.goauthentik.io/start`.
2. In a fresh private window, complete password and passkey authentication.
3. Confirm the browser returns to the original HTTPS hostname, not an internal
   IP address.
4. Complete the application's own login and exercise its normal functions.
5. Test sign-out and a denied Authentik user.
6. Test application API, mobile, webhook and health-check routes. If a client
   cannot perform browser authentication, do not blindly place its route behind
   forward auth; preserve a private direct route or define the narrowest safe
   bypass based on the application's authentication design.
7. Confirm the direct fallback still works, then record the integration as
   tested.

## Path C — keep private without Authentik

Use this for Tailscale, SSH, DNS, NFS/SMB/iSCSI, camera streams and any recovery
interface where an Authentik or NPM outage would prevent repair.

1. Keep the protocol on its private VLAN or trusted management network.
2. Permit access through OPNsense policy and Tailscale only where required.
3. Use the protocol's native authentication, SSH keys or device credentials.
4. Do not create public Cloudflare records or inbound WAN port-forwards.
5. Link to the private address from Homepage only for authorized users.

## Faster rollout without losing control

The recommended faster method is a staged assembly line, not a single bulk
cutover:

1. Create the Authentik groups and standard policies once.
2. Standardize hostnames, NPM TLS settings and the validation worksheet.
3. Build one reusable Authentik blueprint for native-OIDC applications and one
   for per-service forward-auth applications. Keep client secrets outside the
   blueprint and generate a unique secret per application.
4. Create a small, reviewed NPM host-regeneration helper that accepts an
   explicit proxy-host ID and Authentik provider values, saves the prior config,
   performs the API regeneration, runs `nginx -t`, and stops on any error.
5. Replace three manually maintained DNS records per hostname with one
   authoritative internal `elliottrook.com` source that both Pi-holes query.
   Design and test this DNS change separately before relying on it.
6. Onboard applications in batches by pattern, but enable and validate only one
   service at a time.

Authentik also supports domain-level forward auth, which can protect multiple
hostnames with one provider. It is quicker but creates a wider failure and
policy scope and still requires correct NPM routing. Keep per-service providers
until the access rules and rollback process are routine; consider domain-level
forward auth later only for services that genuinely share the same users and
policy.

## Per-service completion record

Add one row only after the complete private-session and rollback tests pass:

| Service | Hostname | Pattern | Direct fallback tested | SSO/gate tested | Non-browser clients tested | Date |
|---|---|---|---|---|---|---|
| Nginx Proxy Manager | `proxy.elliottrook.com` | Forward auth | Yes | Yes | Not applicable | 2026-08-22 |

## Stop conditions

Roll back instead of continuing if any of the following occurs:

- the direct-management URL no longer works
- any resolver returns the wrong address or `NXDOMAIN`
- NPM fails `nginx -t`
- Authentik redirects to an internal HTTP address
- the local break-glass administrator stops working
- a mobile client, API, webhook or automation required for normal operation is
  blocked by the new authentication layer
- the service receives administrator privileges from an unexpected claim or
  group mapping

Do not remove the previous known-good configuration or its backup until the
service has passed the complete checklist.
