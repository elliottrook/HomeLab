# Jellyfin optional browser SSO

Deployed 2026-09-26 on Jellyfin **12.1.0** with Community SSO **5.0.0.0**.
Jason confirmed both account choices work. Post-login checks observed JellyTV
playing as `jason` without pause. Use the
private [browser login](https://jellyfin-sso.elliottrook.com/web/index.html#!/login).

## Choosing an account

The login page offers **Authentik — jason** and **Authentik — elliottrook**.
Both authenticate the existing Authentik owner `jason`, then select the explicitly
linked, existing Jellyfin account. To switch accounts, sign out of the Jellyfin
browser session and choose the other button. An existing Authentik session can
complete the second sign-in without another passkey prompt.

| Jellyfin account | Plugin provider | Authentik application / provider ID | Existing Jellyfin UUID |
|---|---|---|---|
| jason | `authentik-jason` | `jellyfin-jason` / 44 | `329ac173978e43ae8d427d3a561db005` |
| elliottrook | `authentik-elliottrook` | `jellyfin-elliottrook` / 45 | `a4d48b163ede487bba05447e7c0b89da` |

Each Authentik application directly allows only its owner; uncached policy
checks allow `jason` and deny `akadmin`. Both use the existing passkey-only flow,
a confidential authorization-code client, signed tokens and user UUID subjects.
Callbacks are exact `/sso/OID/redirect/<plugin-provider>` paths on the browser
hostname. Plugin links are keyed by provider plus subject, so the two accounts
remain distinct. This is an explicitly authorized owner choice, not arbitrary
username impersonation or automatic account matching.

## Preserving client operation

This is additive browser SSO. Existing server URLs, direct port 8096, passwords,
API keys, native authentication providers and Quick Connect remain available.
NPM does **not** place a forward-auth gate around the client API. The six account
policies and all 24 pre-existing device-token records were unchanged across
installation and after both real SSO logins. JellyTV playback was observed
afterward; this proves that client, not every possible client implementation.

Keep these settings:

- `DisablePasswordLogin=false`, `EnableSingleLogout=false`.
- Per-provider `EnableAuthorization=false`, `DefaultProvider` empty,
  `AllowExistingAccountLink=false`, `SyncUsernameFromProvider=false`.
- Explicit preprovisioned links to the UUIDs above. Unknown identities are
  provisioned disabled as a fail-safe; owner-only Authentik policy and explicit
  links are the normal restriction. No additional account was created.
- `DisableAvatarFromPictureClaim=true`; no profile/avatar synchronization.
- `AllowPrivateNetworkAddresses=true` is required for the private Authentik
  endpoint. HTTPS and issuer verification remain enabled; no endpoint-validation
  relaxation was needed in discovery/start checks.
- Both labelled login buttons are managed by the plugin. Do not replace the
  existing login form, enable global SSO-only enforcement, repoint native auth
  providers or revoke client sessions just to make browser SSO automatic.

The stable plugin was rehearsed with the same installed image in a network-none
fixture without production configuration, media or published ports. Both
provider links and login buttons passed; a conflicting same-provider rebind
returned 409; account policy and token checks passed. The fixture container and
its anonymous volumes were removed.

## Network and service records

The browser hostname is new and private; existing client hostnames were not
repointed. OPNsense and both Pi-holes resolve it to NPM `192.168.50.23`.
NPM host **32** proxies HTTP to TrueNAS `192.168.20.40:8096`, with wildcard
certificate 8, forced HTTPS and WebSockets. Native Jellyfin still authenticates
protected API calls; `/Users` returns 401 with or without spoofed identity headers.

OPNsense rule `3a1ee37e-0288-4b85-8a0e-9323f43b563a` permits only TCP from
NPM to that backend. Its final sequence **2192** precedes the Management VLAN
RFC1918 deny. The first staged sequence fell after that deny; timeout validation
caught it and only the new rule's ordering was corrected. Existing rules and
client routes were not broadened. DNS object:
`1bf4c329-6271-4f6d-8887-7c940bdcf226`.

`check-authentik-browser-boundary.py` now covers 134 DNS, HTTPS, API-denial and
SSO-start checks. Existing Doctor/Prometheus service checks remain unchanged;
this adds no monitoring schedule or public ingress.

## Checkpoints and recovery

Server image retained unchanged:
`sha256:2e68d77a7543f915ea9491497907ffbc9a897d710f96610fc4115bde88d0a189`.
Plugin package SHA-256:
`29bfc6ca2fa76a08f72b724ddf27ef3ea1c853ab087b182da5d67a72ef0e13e9`.

The authoritative `/config` is now `/mnt/Media/appdata/jellyfin`, a dedicated
ZFS dataset. This supersedes the older named-volume discovery in the media
assessment. No server upgrade or volume migration was performed by this step.

- TrueNAS checkpoint `/root/authentik-jellyfin-20260926T225837Z` retains container
  metadata, pre-install policy/credential fingerprints, the database captured at
  restart and the verification report. The partial `config/` file copy is **not**
  the accepted backup.
- Full pre-install snapshot:
  `Media/appdata/jellyfin@authentik-sso-20260926T225837Z`. Restored read-only clone:
  `Media/authentik-jellyfin-restore-20260926T225837Z`, mounted at
  `/mnt/root/authentik-jellyfin-20260926T225837Z/restored-config` behind a 0700
  parent. SQLite/WAL restored from it passed integrity checks with 6 users,
  1,616 watch-state rows and 24 device rows. These are local recovery copies,
  not proof of off-site replication.
- Configured snapshot:
  `Media/appdata/jellyfin@authentik-sso-configured-20260926T231120Z`.
  `sso-config-and-key.tar` in the checkpoint includes the plugin configuration,
  its encryption key and branding; all three files were byte-verified. Keep
  configuration and `data/plugins/SSO-Auth/sso-secret.key` together. Key is 0600;
  protected archives/handoff files must never enter Git or prompts.
- Authentik `/opt/authentik/backups/jellyfin-20260926T230418Z`.
- NPM `/opt/nginx-proxy-manager/backups/jellyfin-20260926T230559Z`.
- OPNsense `/conf/backup/config-jellyfin-sso-20260926T230509Z.xml` and the
  intermediate order checkpoint `/conf/backup/config-jellyfin-sso-order-before.xml`.
- Pi-hole config copies inside the respective containers:
  `/etc/pihole/pihole.toml.before-jellyfin-sso-20260926T230939Z` and
  `/etc/pihole/pihole.toml.before-jellyfin-sso-20260926T230940Z`.

For an SSO fault, use the unchanged native login/client route first. Disable
only the two new SSO providers and managed buttons if needed; native passwords
were never replaced. Restore the plugin configuration and encryption key as a
pair when repairing links. Removing the plugin requires another planned restart.
Do not roll the whole database back merely to undo SSO: that would discard new
watch history. A full disaster recovery uses the retained exact image and full
configuration snapshot, then verifies native login, accounts, clients and both
SSO links before promotion.

Upstream references: [stable release](https://github.com/Flowfin/jellyfin-plugin-sso/releases/tag/5.0.0-JF12-stable),
[provider setup](https://github.com/Flowfin/jellyfin-plugin-sso/wiki/Provider-Setup),
[client compatibility](https://github.com/Flowfin/jellyfin-plugin-sso/wiki/Client-Compatibility).

## Acceptance and discovery — 2026-09-26

Jason confirmed both account choices work. The post-login check retained all six
account policies, native credential fingerprints and all 24 original device
tokens, with Quick Connect enabled and JellyTV actively playing as `jason`.
Homepage now opens the private browser login above; only its Jellyfin `href`
changed. Other configuration bytes, including widget settings, were preserved.
Homepage checkpoint: `/opt/homepage/backups/jellyfin-promote-20260926T231857Z`.

AI administration: not currently supported through a dedicated broker identity.
This deployment used the approved source-local administrative API credential
without exposing it. It does not create ongoing autonomous administration or
credential release; human recovery retains native administration. No VM, IP,
VLAN or physical inventory changed; the new DNS/proxy objects are recorded above.
