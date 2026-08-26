# Authorization

## Authentik-protected Nginx Proxy Manager

**Status: TESTED AND WORKING — 2026-08-22**

Nginx Proxy Manager (NPM) is the first service protected by Authentik. This is
a forward-auth integration rather than native SSO, so NPM retains its own
login after Authentik grants access.

Tested authentication path:

```text
https://proxy.elliottrook.com
  -> Authentik password
  -> WebAuthn/passkey
  -> NPM credentials
  -> Nginx Proxy Manager
```

The complete password, passkey and NPM-login sequence was validated in a fresh
private browser session on 2026-08-22.

## Known-good configuration

### TLS certificate

NPM uses a Let's Encrypt wildcard certificate issued through the Cloudflare
DNS-01 challenge. The certificate contains both names:

- `*.elliottrook.com`
- `elliottrook.com`

Keep the Cloudflare API credential private and grant only the DNS permissions
needed for certificate issuance and renewal. The certificate was successfully
attached to NPM proxy host #2 and served for `proxy.elliottrook.com`.

### Proxy host #2

| Setting | Value |
|---|---|
| Public name | `proxy.elliottrook.com` |
| Forward scheme | `http` |
| Forward address | `192.168.50.23` |
| Forward port | `81` |
| TLS | Wildcard Cloudflare DNS-01 certificate |
| Authentication | Authentik forward auth |
| Application login | NPM credentials remain enabled |

The destination appears to point back to the NPM host because NPM is placing
its own administration interface behind a named HTTPS proxy host. Direct
`http://192.168.50.23:81` access is retained as an administrative fallback and
rollback path; it must remain restricted to trusted management networks.

### Internal DNS

The following local record exists in every active internal resolver:

```text
proxy.elliottrook.com -> 192.168.50.23
```

It was added to:

- OPNsense Unbound host overrides
- Pi-hole #1 local DNS records
- Pi-hole #2 local DNS records

All three copies are currently required. A missing record on either Pi-hole
causes intermittent `NXDOMAIN` results depending on which resolver a client
uses. This duplication should eventually be replaced by one authoritative
internal source that both Pi-holes query.

Validate each configured resolver directly, not only the client's default:

```sh
dig @192.168.50.1 proxy.elliottrook.com
dig @192.168.20.20 proxy.elliottrook.com
dig @192.168.20.40 proxy.elliottrook.com
```

Each answer must contain `192.168.50.23`. If command-line resolution succeeds
but a browser still fails, flush the client DNS cache and use a new private
window before changing the servers.

### Authentik

NPM has an Authentik proxy provider/application assigned to the embedded
outpost. The NPM host uses Authentik only as an authorization gate; it does not
send `X-authentik-*` identity headers to NPM because NPM does not consume them
and its own authentication remains authoritative.

The embedded outpost must have the following complete external URL:

```text
authentik_host = https://auth.elliottrook.com
```

Configure it at **Authentik Admin > Applications > Outposts > authentik
Embedded Outpost > Edit**. The `https://` scheme is required. With the detected
internal value, Authentik redirected the browser to
`http://192.168.50.22:9000/...`; WebAuthn correctly rejected that insecure
origin even though the original NPM page used HTTPS. Setting `authentik_host`
to the external HTTPS URL fixed the redirect and passkey flow.

### 2026-08-25 WebAuthn HTTPS error follow-up

A later recurrence report was initially misdiagnosed as the same reverse-proxy
scheme problem. Inspection confirmed that Authentik 2026.8.0 was already using
the correct system-wide Base URL and embedded-outpost host:

```text
Base URL = https://auth.elliottrook.com
authentik_host = https://auth.elliottrook.com
```

NPM proxy host `auth.elliottrook.com` was also confirmed to forward internally
to `http://192.168.50.22:9000`. Its custom configuration now explicitly
preserves the browser-facing request metadata:

```nginx
proxy_set_header Host $http_host;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

Those headers are correct defensive configuration, but they were not the cause
of the observed error. The failing launch came from a dashboard shortcut that
opened Authentik's direct management fallback at
`http://192.168.50.22:9000`. WebAuthn correctly refuses that insecure origin.
Opening `https://auth.elliottrook.com` produced the passkey prompt and completed
authentication successfully. The dashboard shortcut was updated to the HTTPS
hostname.

Keep `http://192.168.50.22:9000` available on the trusted management network as
a recovery path, but do not publish or use it as the normal Authentik launch
URL. Passkey authentication is expected to fail on that direct HTTP endpoint.

## NPM hidden `advanced_config` workaround

The installed NPM release does not expose the custom Advanced text field in
the GUI, although proxy host #2's `advanced_config` database field still exists.
The working configuration was therefore updated through the terminal and the
host was regenerated through NPM's API.

This is an exceptional recovery procedure, not the normal editing workflow:

1. Confirm direct NPM access on `http://192.168.50.23:81` before starting.
2. Back up `/opt/nginx-proxy-manager/data/database.sqlite` while it is in a
   consistent state. Also export host #2 through the API and save the existing
   `advanced_config` separately.
3. Update only `proxy_host.id = 2` in SQLite. Do not replace the whole database
   and do not edit generated `/data/nginx/proxy_host/2.conf` directly.
4. Obtain a short-lived NPM API token without recording its value in shell
   history, documentation or Git.
5. `GET /api/nginx/proxy-hosts/2`, retain the accepted editable fields, then
   `PUT` the payload back to `/api/nginx/proxy-hosts/2`. The `PUT` is what
   regenerates `/data/nginx/proxy_host/2.conf` from the database value.
6. Run `nginx -t`, inspect the generated host #2 configuration, and restart or
   reload NPM if its workers have not picked up the regenerated file.
7. Test with a fresh private browser session before removing any backup.

The final forward-auth block must include these behaviours:

- protect `/` with `auth_request /outpost.goauthentik.io/auth/nginx`
- send unauthenticated requests to the Authentik start endpoint
- proxy `/outpost.goauthentik.io` to `http://192.168.50.22:9000`
- preserve `Host`, `X-Forwarded-Proto` and `X-Forwarded-For`
- preserve the original HTTPS return URL
- omit `X-authentik-*` identity propagation to NPM

Validation commands on the reverse-proxy host:

```sh
docker exec nginx-proxy-manager nginx -t
docker exec nginx-proxy-manager sh -c \
  'grep -n -A90 "server_name proxy.elliottrook.com" /data/nginx/proxy_host/2.conf'
```

The generated configuration should contain the Authentik locations and report
successful Nginx syntax validation. A `302` from `/` to
`/outpost.goauthentik.io/start` is expected for an unauthenticated request.

## Rollback and recovery

Before any future change, preserve both the NPM database and a text copy of
host #2's previous `advanced_config`. Database copies and API exports may
contain sensitive host configuration and must remain in protected backup
storage outside Git.

Rollback order:

1. Keep or restore trusted-network access to `http://192.168.50.23:81`.
2. Restore only the saved host #2 `advanced_config` through the database/API
   regeneration workflow; restore the entire database only when the database
   itself is damaged or the targeted rollback cannot succeed.
3. Validate with `nginx -t`, reload NPM and confirm direct NPM login.
4. Confirm `proxy.elliottrook.com` presents the wildcard certificate.
5. Confirm the unauthenticated `302`, Authentik login and final NPM login.

Do not make database changes without a recoverable copy. Do not store the NPM
API token, Cloudflare token, Authentik credentials, passkey material or raw
database backup in this repository.

## Troubleshooting lessons

- Test DNS against OPNsense and both Pi-holes independently. A correct OPNsense
  answer does not prove a client using Pi-hole can resolve the name.
- A browser TLS warning followed by “server not found” can be stale negative DNS
  caching. Verify with `dig` and, when necessary, test with `curl --resolve`
  before editing NPM.
- `nginx -t` proves syntax, not that running workers reloaded the new file.
- NPM's generated configuration is disposable. Persist the change in
  `advanced_config`, then use the API to regenerate it.
- Forward-auth does not replace an application's native login. The second NPM
  credential prompt is expected.
- Do not forward identity headers to an application that does not use them.
  The minimal authorization-only configuration restored normal NPM login.
- WebAuthn failures mentioning HTTPS must be diagnosed from the browser's
  actual authentication URL and from the link that launched it. An internal
  `http://192.168.50.22:9000` URL can be either a bad Authentik redirect or a
  dashboard/bookmark pointing directly at the recovery endpoint; distinguish
  those cases before changing the proxy.
- Dashboard and bookmark entries must use `https://auth.elliottrook.com`.
  Retaining the direct HTTP management path for recovery does not make it a
  valid WebAuthn origin.
- Change one layer at a time and keep the known-good direct-management path
  available throughout testing.

For future services, prefer native OIDC/OAuth2 integration when supported so
Authentik can replace the application's password instead of adding a second
gate. Use forward auth for services without suitable native SSO support.
