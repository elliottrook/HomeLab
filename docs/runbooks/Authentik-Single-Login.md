# Authentik single-login browser cohort

Deployed 2026-09-23 under the approved Stream A rollout and Jason's explicit
request for passkey/Face ID only. Human workflow acceptance remains pending.
See [the rollout project](../projects/Authentik-Rollout.md) for authoritative
status and the wider project's remaining gates.

## Normal use

Use the Homepage tiles or these HTTPS names. Old IP/port browser addresses now
redirect here. Authenticate with the existing Authentik passkey; subsequent apps
can reuse the Authentik session without another prompt.

| Application | Browser address | Application identity |
|---|---|---|
| Dozzle | `https://logs.elliottrook.com` | Verified `jason` proxy identity |
| Homarr | `https://homarr.elliottrook.com` | Existing `jelliott` account, native OIDC |
| Code Server | `https://code.elliottrook.com` | Existing editor configuration/workspace |
| Dockge | `https://dockge.elliottrook.com` | Existing sole owner `elliottrook` |
| File Browser | `https://files.elliottrook.com` | Existing `elliottrook`, user ID 2 |
| NetBox | `https://netbox.elliottrook.com` | Existing `admin`, user ID 1 |

No app password is required on these browser paths. Authentik's shared
`aster-companion-passwordless` flow contains identification, WebAuthn validation
and user-login stages; this deployment references it without modifying it.
Other previously graduated services retain their earlier configuration.

## Access boundary

NPM hosts 19–24 retain owner-only forward authentication. NPM sets
`X-Homelab-Authentik-User` from the successful auth subrequest's
`X-Authentik-Username` response, replacing any supplied client header.
Each browser ingress requires both actual TCP source `192.168.50.23` and the
verified username `jason`. Other TCP sources receive a same-service HTTPS
redirect; missing/wrong identity from NPM receives 403. Forwarded IP headers
are not used to establish the trusted source.

The six application containers have no published host ports. Ingress containers
publish the former IPv4 ports. They use pinned nginx
`sha256:608a100c71651bf5b773c89083b4a1ad7ef4b2bd05d7a7e552271e03123692ad`,
UID/GID 101, a read-only root, temporary `/tmp`, dropped capabilities and
`no-new-privileges`. Docker restart policies retain this boundary after a
normal restart; a full host reboot has not been tested for this milestone.

NetBox is the deliberate API exception: ingress forwards `/api/` to NetBox,
which retains its API authentication and permissions. It also publishes
`127.0.0.1:8000` for the loopback-only Aster reader. This exception does not
grant browser identity through headers. Do not remove localhost without
checking `aster-netbox-report.service`.

## Deployment and recovery material

| Host | Declarative configuration / state |
|---|---|
| TrueNAS | `/mnt/Media/appdata/authentik-browser-ingress/{dockge,filebrowser,dozzle}/nginx.conf`; `compose.json` in the parent describes the three existing standalone ingress containers for recreation |
| TrueNAS Dockge | Catalog app `network.web_port.bind_mode=exposed`, external `authentik-dockge-ingress`; existing database `/mnt/Media/appdata/dockge/dockge.db`, setting `disableAuth=true` |
| TrueNAS File Browser | Catalog app exposed port, external `authentik-filebrowser-ingress`; `/mnt/.ix-apps/app_mounts/filebrowser/config/filebrowser.db`, proxy auth header `X-Homelab-User`; ingress maps the verified owner to `elliottrook` |
| TrueNAS Dozzle | `/mnt/Media/appdata/dockge/new_arr/compose.yaml`, only the Dozzle service changed; external `authentik-dozzle-ingress`; `/mnt/Media/appdata/dozzle:/data`; forward-proxy identity header |
| LXC 100 Code Server | `/opt/code-server/compose.json` and `authentik-ingress/nginx.conf`; original container retained stopped as `code-server-pre-authentik` with restart policy `no` |
| LXC 100 Homarr | Existing `/opt/homarr/compose.yaml` plus automatic `compose.override.yaml`; ingress config below `/opt/homarr/authentik-ingress`; protected OIDC files below `/opt/homarr/secrets` |
| LXC 111 NetBox | Existing `/opt/netbox/docker-compose.yml` plus `docker-compose.override.yml`; ingress config below `authentik-ingress`; OIDC configuration in `configuration/zz_authentik.py` and protected `authentik-oidc.json` |

TrueNAS rejects loopback host bindings for these catalog apps. Use its supported
exposed/private-network mode; do not substitute a delayed firewall script.
Create the three named external Docker networks before restoring the catalog
apps/Dozzle and their ingress. Existing ingress containers were started directly
with Docker, so the recovery Compose declaration is not their current Compose
owner. Recreate only a missing or deliberately stopped/removed ingress instance
with that declaration; do not tear down the application or shared stacks.

Homarr's hidden native provider 35 (`homarr-native`) uses strict callback
`https://homarr.elliottrook.com/api/auth/callback/oidc`; NetBox provider 36
(`netbox-native`) uses `https://netbox.elliottrook.com/oauth/complete/oidc/`.
Both explicitly link Authentik subject `8` to existing accounts. Homarr keeps
credentials-owned data/groups and disables credentials as a login provider;
automatic email account linking is not enabled. NetBox protects its existing
username/email/name fields from social-auth updates. No new admin account was
created in either app. Keep client secrets on their source hosts.

Protected pre-change checkpoints:

- TrueNAS: `/root/authentik-single-login-20260923T191107Z` contains catalog app
  settings, container metadata, Dockge/File Browser databases and original
  `new-arr-compose.yaml`. Earlier `/root/authentik-admin-cohort-20260923T184209Z`
  also contains application recovery material.
- Homarr: `/opt/homarr/backups/single-login-20260923T192940Z` contains original
  Compose and an integrity-checked database before the explicit OIDC link.
- Code Server: `/opt/code-server/backups/single-login-20260923T192350Z` contains
  original container metadata; earlier `authentik-rollout-20260923T184208Z`
  contains its configuration checkpoint.
- NetBox: `/opt/netbox/backups/single-login-20260923T193123Z` contains the
  pre-ingress override; `authentik-rollout-20260923T184211Z` contains its
  PostgreSQL/configuration checkpoint before SSO linkage.
- NPM: `/opt/nginx-proxy-manager/backups/single-login-20260923T191659Z` precedes
  verified-header changes. Restore only target host records, not the whole live
  database over concurrent project work.
- OPNsense: `/root/authentik-netbox-oidc-20260923T192742Z` precedes the exact
  NetBox-to-NPM HTTPS rule `67302b29-9f46-413a-8753-c791ef3a9070`.
- Homepage: `/opt/homepage/backups/single-login-20260923T193332Z` preserves the
  previous service file. Only six `href` values changed; widget settings did not.

## Targeted rollback and emergency access

Use existing SSH access and `docker exec`/private Docker networks for recovery.
Do not republish a passwordless backend to regain access. Stop on an unreadable
checkpoint; do not replace current production databases just to reverse an
authentication setting.

1. Restore application authentication while the backend remains private:
   reset Dockge's `disableAuth` setting and restart its app; use the File Browser
   CLI against its stopped database to restore the checkpoint's auth method;
   restore Homarr's previous provider configuration if needed. Preserve current
   users, permissions, files and integrations. NetBox's existing local password
   remains available only through deliberate private recovery access.
2. If reverting Code Server, retain an authenticated ingress or configure its
   native password first. Its original container was already passwordless;
   starting it on the old public host binding would reintroduce the bypass.
3. Only after proving the restored authentication may an explicitly chosen
   ingress be removed and its original host binding restored. Stop the owning
   ingress first to avoid a port conflict; never recreate an entire unrelated
   Compose stack or TrueNAS catalog set.
4. Remove only the explicit native OIDC account links/providers if rolling back
   those integrations. Keep app accounts and the existing forward-auth gate.
   Providers 28–33 previously had a null authentication-flow override. Restore
   those fields only if intentionally reverting passkey-only selection; never
   edit the shared Companion flow as part of rollback.
5. Reverse only this project's exact NPM settings, DNS/rule objects or Homepage
   links when required. Retain the NetBox HTTPS return rule while native OIDC
   uses it. Check Aster's NetBox reader after any network change.

Before declaring recovery successful, check direct-IP denial/redirect, owner
access, non-owner denial, app identity/roles, normal workflows, sign-out and
the affected API integrations. Human Face ID and application acceptance cannot
be inferred from HTTP redirects alone.
