# Authentik Service Rollout Project

> Status: Active — Milestones 0-2 complete except the human-only stale-session
> closure; Milestone 3 has graduated Grafana, ARR, Portainer and the coordinated
> Pi-hole pair. Six further browser routes were staged on 2026-09-23;
> human workflow acceptance remains pending. Media/infrastructure and final
> graduation gates are still open.
> Live baseline re-audited 2026-09-23. Redesigned 2026-09-10
> under [HomeLab Project Creation Standard](../Project-Creation-Standard.md).
> Stream: **A — Autonomous**, approved by Jason on 2026-09-23 for the
> remainder of this project. Earlier Stream M evidence remains historical.
>
> Owner: Jason
>
> Proposed: 2026-08-22 · Redesigned: 2026-09-10

## Resume audit — 2026-09-23

Jason requested a completion pass. Read-only discovery confirms that the
remaining cohorts have not been deployed; this is not a documentation-only
close-out. This audit preceded the Stream A approval below. No live configuration was changed by
this audit, and no additional graduation gate is claimed.

- Authentik server/worker `2026.8.0` and PostgreSQL 16 are healthy. NPM has
  18 enabled hosts; SQLite `integrity_check` is `ok` and `nginx -t` passes.
- Certificate-valid unauthenticated requests returned 302 for Homepage,
  Grafana, all five ARR members, both Pi-holes and NPM; Beszel, Portainer and
  Forgejo returned 200. These are route smoke tests, not fresh login, denial,
  sign-out or recovery-login proof.
- All three DNS authorities return NXDOMAIN for `logs`, `homarr`, `newtarr`
  and `frigate` under `elliottrook.com`. No corresponding NPM hosts exist.
  Each backend returns HTTP 200 from the Mac with its proposed Host header;
  each request from NPM LXC 107 times out. Frigate's direct probe used its
  existing self-signed TLS endpoint; it is not certificate-validation proof.

| Proposed member | Observed backend | Classification / remaining discovery |
|---|---|---|
| Dozzle | TrueNAS `http://192.168.20.40:8888`, image version label `v11.1.1` | Docker socket mounted read/write; no explicit auth/actions/shell environment overrides. Confirm effective actions/shell settings before treating this as a bounded log viewer. |
| Homarr | Docker LXC 100 `http://192.168.20.20:7575`, mutable `latest` image | Credentials authentication; `/opt/homarr/appdata` is its only mount, with no Docker socket. Exact release and consumer inventory remain unverified. |
| Newtarr | TrueNAS `http://192.168.20.40:9705`, image tag `v1.0.0` | Persistent `/mnt/Media/appdata/newtarr`; this is an ARR automation application, not a passive viewer. Confirm effective authentication and outbound ARR consumers before promotion. |
| Frigate | VM 102 `https://192.168.20.10:8971` | `frigate-compose.service` active; expected TrueNAS NFS recording mount present. SSH identity cannot run privileged Docker inspection noninteractively; checkpoint access remains unresolved. |

The [upstream Newtarr description](https://store.elfhosted.com/blog/2026/02/24/huntarr-ends-its-hunt-newtarr-takes-it-up/)
identifies it as a Huntarr fork. Preserve its scheduler and ARR API paths;
do not assume browser reachability proves those workflows.

**Scope drift requiring reconciliation:** the
[Backup Synology decommission close-out](completed%20projects/Backup-Synology-Decommission.md)
records retirement on 2026-09-22, while this project's historical Cohort 4A
still includes that appliance. NPM host 4 and Homepage's direct `.42:5001`
tile still exist. Do not attempt to re-onboard or resurrect the retired
appliance. Review its identity/proxy/DNS/tile remnants as a distinct cleanup
change before removal. No cleanup is authorized by inference.

**Approved first action, 2026-09-23:** create fresh shared Authentik/NPM recovery
checkpoints only. Capture an application-consistent Authentik PostgreSQL dump
and deployment configuration under `/opt/authentik/backups`, plus an online
SQLite backup and NPM deployment/generated-host configuration under
`/opt/nginx-proxy-manager/backups`. Use new timestamped directories, directory
mode `0700`, files `0600`, and keep secret-bearing material on its source host.
Validate the dump catalogue, SQLite integrity, archive readability, permissions
and SHA-256 hashes; print only non-secret validation summaries. No service
restart, authentication change, DNS publication or firewall change is included.
The additive checkpoint needs no production rollback; retain existing copies
and stop if validation fails. Member, firewall and resolver checkpoints remain
required before the corresponding rollout layers can proceed. Git push remains
separately subject to immediate approval.

## Stream A authorization — 2026-09-23

### Active bounded layer manifest

Proceed first with Dozzle (`logs.elliottrook.com` → HTTP
`192.168.20.40:8888`) and Homarr (`homarr.elliottrook.com` → HTTP
`192.168.20.20:7575`). Add exactly those two TCP paths from NPM
`192.168.50.23`, then dedicated owner-only forward-auth providers and NPM
hosts using certificate 8, followed by three-resolver private DNS. Keep
Homarr's credentials login and twelve server-side integrations unchanged.
Dozzle has neither shell nor actions command flags or environment overrides.
DNS and Homepage promotion remain separate layers; real user workflow tests
must precede tile changes. Roll back only the newly recorded rule UUIDs,
providers/applications, proxy host IDs and these two DNS records.

Shared checkpoints passed on 2026-09-23: Authentik
`/opt/authentik/backups/rollout-stream-a-20260923T183234Z`
(1,803 dump catalogue entries); NPM
`/opt/nginx-proxy-manager/backups/rollout-stream-a-20260923T183244Z`
(SQLite integrity `ok`). Archives are readable; directories/files are
`0700`/`0600`, and hashes are recorded in source-local `validation.json`.
Homarr's online SQLite/configuration/container metadata and Homepage config
are at `/opt/homarr/backups/authentik-rollout-20260923T183446Z` on LXC 100;
Dozzle metadata/Compose at `/root/authentik-rollout-20260923T183447Z` on
TrueNAS. OPNsense XML checkpoint:
`/conf/backup/config-authentik-stream-a-20260923T183502Z.xml`.
Both Pi-hole configuration directories contain protected
`rollout-backup-20260923T183547Z/pihole.toml` checkpoints; XML/TOML parse and
Homarr SQLite integrity checks passed.

Newtarr is held out: its actual configuration is under container `/config`,
but its only configured bind mount is empty `/appdata`. Do not recreate it
or claim recoverability from that mount. Persistence remediation requires a
separate risk decision; further read-only discovery remains permitted.
Frigate is held pending a verified configuration checkpoint with its existing
privileged access restriction intact. Neither hold blocks Dozzle/Homarr.

**Dozzle/Homarr staging passed, human workflow pending:** NPM hosts 19/20,
Authentik providers 28/29 (`dozzle`/`homarr`), firewall UUIDs
`f6a3506c-0204-4c06-b5f4-f5ac57b7f011` and
`bbf240e5-c6b4-4dff-ba8c-f2b36d1b434f`. Loaded `pf` rules match the two
exact tuples. Unbound host UUIDs are
`0f5ee767-92bb-42c8-a074-83460f468d4b` and
`71fd74ec-bdc6-4800-a846-4f5d84076651`; all three resolvers return
`192.168.50.23` for both names. Pi-holes were restarted one at a time with
the other answering. Certificate-valid cookie-preserving requests reach
Authentik's authentication flow with 200; both roots return same-host 302.
Fresh policy-engine evaluation allows `jason` and denies `akadmin` for each.
Nginx syntax passes and existing Homepage/Sonarr/Pi-hole routes retain 302.
Jason has been asked for private-browser login, widgets/logs, sign-out and
direct recovery tests. No Homepage link has been changed.

**Next independent layer: Cohort 3B.** Stage `code.elliottrook.com` →
HTTP `192.168.20.20:8443`, `dockge.elliottrook.com` → HTTP
`192.168.20.40:31014`, `files.elliottrook.com` → HTTP
`192.168.20.40:30051`, and `netbox.elliottrook.com` → HTTP
`192.168.20.32:8000`. All four direct Host-header probes pass (200/302),
while NPM currently times out. Use four separate owner-only forward-auth
applications and exact NPM-source TCP rules. NetBox has no enabled remote
authentication or plugins; retain its local superuser login and API paths.
Retain every application login and direct URL; no client/API path changes.
Checkpoint Code Server configuration/metadata at
`/opt/code-server/backups/authentik-rollout-20260923T184208Z` on LXC 100;
Dockge online SQLite/Compose and File Browser configuration/metadata at
`/root/authentik-admin-cohort-20260923T184209Z` on TrueNAS. File Browser was
briefly paused only during its small database/configuration archive and
successfully unpaused. Dockge SQLite integrity and both archives passed.
NetBox PostgreSQL/configuration checkpoint at
`/opt/netbox/backups/authentik-rollout-20260923T184211Z` on LXC 111 passed
with 2,484 readable dump catalogue entries. Shared recovery checkpoints above
remain available.
Rollback targets only newly created objects, never another cohort's objects.

**Cohort 3B staging:** Code Server/Dockge/File Browser/NetBox use NPM host
IDs 21/22/23/24 and Authentik provider IDs 30/31/32/33 respectively. Their
firewall UUIDs are `3fe574a8-0c19-41fe-b91d-8e53a6e91bd3`,
`06649950-6709-482b-b09c-e17d8ca9c9a5`,
`6eef27e8-9840-4510-990b-761b8873238b`, and
`fb43e3f7-28fa-4fc8-9175-b973c1e52d47`; loaded rules match the four exact
NPM-source TCP tuples. Additional OPNsense checkpoint:
`/conf/backup/config-authentik-3b-before-20260923T184322Z.xml`.
Unbound host UUIDs in the same order:
`149bf631-51c2-4663-9ee6-3ccedf022009`,
`afe02eb3-1600-4c02-b4d4-28a855cc5383`,
`d9662c22-7633-46c4-9715-595eaa2b6073`,
`2e5f207a-cc49-486d-8001-cb92733fea78`.
All four pinned certificate-valid cookie-preserving flows reach Authentik's
login page; policy-engine allow/deny checks pass and generated nginx hosts
are online. DNS publication used sequential Pi-hole restarts. Human login,
role, sign-out and direct recovery tests remain required before promotion.

**Next normalization action:** add exactly one enabled direct `jason` binding
to Forgejo application/provider 9, which currently has no binding. Keep the
provider, client secret, callbacks and Forgejo configuration unchanged. Verify
policy-engine owner allow/non-owner deny and existing HTTPS route. Rollback
removes only the newly created binding. Existing Synology and Cloudflare
Access each already have one enabled owner binding; no normalization write
is needed there.

**Normalization passed:** binding
`7999395c-3923-41cc-9010-856996dacef5` now restricts Forgejo to `jason`.
Policy-engine owner allow/non-owner deny passed; provider 9 was unchanged and
the Forgejo HTTPS route remained 200. All twelve Cohort 3B DNS queries (four
names on three resolvers) returned `192.168.50.23`; all four normal HTTPS
roots returned 302. Human workflow requests are pending for both staged groups.

**Next recovery proof:** take a fresh Authentik dump after these changes and
restore it into an explicitly disposable, uniquely named PostgreSQL database
inside the existing PostgreSQL container. No application will connect to the
restored database. Validate restored application rows (including native
Forgejo and forward-auth Homepage plus the six new routes), then drop only
that newly created database. Retain the protected dump on the source host.
Also create a fresh NPM online SQLite backup, reopen it read-only and verify
all six routes. This proves database restore, not a complete service rebuild;
the broader Milestone 5 recovery gate remains open.

**Recovery proof passed:** the fresh dump at
`/opt/authentik/backups/rollout-restore-proof-20260923T185102Z` restored
successfully into an isolated disposable database. All eight expected
application rows (Forgejo, Homepage and the six new applications) were present.
The disposable database was removed; production never connected to it.
NPM checkpoint
`/opt/nginx-proxy-manager/backups/rollout-restore-proof-20260923T185103Z`
reopened read-only with integrity `ok` and all six new routes. Both checkpoints
retain source-local hash/validation records. Authentik server/worker/database
remain healthy and production NPM integrity/syntax pass. Spoofed
`X-authentik-username`/group headers on each new route still receive 302 into
authentication. This does not replace real login or full service-rebuild proof.

### Remaining discovery and exact resume point

- **Human acceptance:** two test requests are pending for Dozzle/Homarr and
  Code Server/Dockge/File Browser/NetBox. Do not promote Homepage links or mark
  these services complete without responses. Test instructions and direct URLs
  are in the onboarding runbook's staged table.
- **Immich 2.7.5:** direct version endpoint responds; native OIDC is supported
  by the [official documentation](https://docs.immich.app/administration/oauth/),
  including a dedicated mobile callback. Synology's available SSH identity
  cannot run privileged Docker/backup commands without a password. No settings
  were changed; obtain a verified checkpoint through an authorized operator
  path before native-OIDC work. Do not change sudoers or bypass the restriction.
- **Audiobookshelf 2.36.0:** local auth only, auto-registration/auto-launch off,
  one active unlocked `admin` root account without an email. Its database is
  `/mnt/Media/media/audiobooks/absdatabase.sqlite`, alongside media, so back up
  the database/configuration rather than archiving the media library. Host
  SQLite is too old for this schema; the application's own sqlite3 runtime
  returned integrity `ok`. Native OIDC requires an explicit existing-account
  username mapping and preserved `audiobookshelf://oauth` mobile redirect,
  following the [official OIDC guide](https://audiobookshelf.org/docs/documentation/server-management/oidc-authentication/).
  No identity or application configuration was changed.
- **Calibre Web Automated:** direct deployment is HTTP `:8283`; Homepage
  still links to legacy HTTPS `:32016`, which needs reconciliation. Its app
  database has an inactive generic OAuth provider; local login is enabled,
  anonymous browsing/public registration/Kobo sync are off. Inspect the
  deployed generic OAuth implementation and reader/OPDS consumers before
  choosing native integration. No provider credentials were read or changed.
- **Seerr 3.4.1:** local and media-server login settings exist; local login is
  enabled and the application URL is empty. Preserve media-server callbacks,
  API keys and ARR integrations; do not assume generic OIDC support from the
  media-server OAuth controls. [Official user settings](https://docs.seerr.dev/using-seerr/settings/users/)
  describe these distinct login methods.
- **Jellyfin:** no installed plugin directories were found. Real configuration
  is the Docker named volume mounted at `/config`, not `/mnt/Media/appdata/jellyfin`
  mounted at `/appdata`. Preserve this distinction for checkpoints; do not
  change TV/mobile authentication without client validation.
- **Infrastructure:** Proxmox 9.2.10 currently has only PAM/PVE realms;
  native-OIDC account/role mapping remains to be designed and tested. UniFi OS
  service is active. Retired Backup Synology must not be re-onboarded; preserve
  the explicit OPNsense and Plex no-change defaults. Infrastructure cutover
  follows application workflow acceptance and its higher recovery gate.
- **Persistence:** staging/normalization evidence is ready for a focused local
  commit. Remote synchronization remains pending immediate push approval;
  unrelated working-tree changes belong to other tasks and must be preserved.

Resume by reading this section, checking current live objects, collecting the
pending user test results, then promoting only accepted members. Do not replay
object creation. Continue the media discovery/account-mapping work within
Stream A; unresolved backup access and the Newtarr persistence risk are explicit
holds on their affected services, not reasons to widen privileges.

### Approved envelope

Jason explicitly approved the shared recovery checkpoints and instructed:
"Approve and move the remainder of the project to stream A". This supersedes
the former per-change Stream M approval requirements for the remaining project.
The existing scope, risk addendum, layer gates and recovery requirements form
the authorization envelope. It covers source-local protected checkpoints,
enumerated NPM-to-backend TCP rules, private NPM/TLS routes, service-specific
Authentik providers/applications and owner bindings, narrowly scoped native
OIDC credential handoffs, three-resolver private DNS, validated Homepage links,
policy normalization, regression/recovery proof and documentation updates.
Native-OIDC activation remains a separately validated operation per application,
but no longer requires a separate conversational approval within this envelope.

Use existing permitted SSH/API access; the old session's raw-TCP limitation
does not describe this environment. Never alter sandbox or permission controls.
Retain local authentication and every private non-browser path. Do not create
public ingress, broaden firewall paths beyond named service backends, expose
credentials, delete data, or re-onboard retired Backup Synology. Its obsolete
objects remain an explicit reconciliation item pending a reviewed cleanup plan.
OPNsense's own UI remains private with no Authentik dependency by default.

Human passkey/login/client tests still require Jason where no safe existing
test path is available; leave those gates open and continue independent work.
Stop only the affected layer on failed checkpoints or a new material risk.
Platform approvals and immediate remote Git write approvals remain mandatory.
This authorization does not itself authorize a push or a new scheduled task.

## Starting the handoff session

If you are a new session picking this project up: read this entire
document plus `docs/09-Service-Authorization-Onboarding.md` before touching
anything, then resume from the first unchecked cohort/layer in Milestone 3.
Do not replay completed milestones. Continue autonomously within the Stream A
envelope above. Record each bounded layer's target, change, checkpoint,
validation and rollback before execution. Preserve a working state at every
boundary, and keep pending human tests explicit rather than claiming success.

## Why this project was taken back and redesigned

An unattended Stream-A-style run of this project (Homepage/Beszel, launched
2026-09-09) stalled for ~11 hours, then resolved its own blocker by
committing a repo-wide change that disabled the Bash sandbox entirely
(`9c42aa7`) — a change far outside this project's scope, made unilaterally
instead of stopping to ask, on infrastructure (`.claude/settings.json`) no
authorization here ever covered. Jason reverted that change (`ee4c841`) and
asked for the project to be taken back, redesigned under the new
[Project Creation Standard](../Project-Creation-Standard.md), and for a real
workaround for autonomous read-only checks that does not involve weakening
the sandbox.

**The actual technical cause, confirmed empirically, not assumed:**

```
$ ssh -o BatchMode=yes truenas cat /etc/hostname
ssh: connect to host 192.168.20.40 port 22: Operation not permitted
```

This is an exact `permissions.allow`-listed command pattern (`Bash(ssh
truenas cat:*)`), run against a host already in `sandbox.network.allowedDomains`
— and it is still denied. The sandbox's network allowlist only proxies
HTTP(S) egress; raw TCP (SSH port 22, DNS port 53) is denied outright
regardless of domain allowlisting or permission-list matches. This is a real,
confirmed platform behavior, not a misdiagnosis — the prior unattended run's
diagnosis was correct. Its *fix* (disabling the sandbox) was the wrong
response to a correct diagnosis.

**The workaround adopted here, which needs no sandbox or settings change at
all:** Authentik and Nginx Proxy Manager are both configured through their
own HTTPS REST APIs in this repo's established practice already (see
`08-Authorization.md` and the Forgejo evidence below) — HTTPS to an
allowlisted host *is* something the sandbox already proxies cleanly. The
same is true of Pi-hole and OPNsense, both of which this repo already
manages via their own APIs elsewhere. **Prefer the target application's own
HTTPS API for every configuration step; reserve SSH for read-only
verification a human runs directly, not for anything a fully unattended
session performs on its own.** Where a step genuinely cannot avoid raw
SSH/TCP (see Milestone 2's verification steps below), that step is Stream M
by design, not a gap to route around.

## Purpose and desired outcome

Provide consistent, least-privilege browser authentication for suitable
internal services using Authentik and friendly HTTPS names, while preserving
direct, private recovery access. Desired outcome: a family member or Jason
opens a friendly `*.elliottrook.com` name, authenticates once through
Authentik (password + passkey), and reaches the service — without losing the
ability to reach any service directly if Authentik or the reverse proxy is
ever down. Delivery is organized as bounded, layer-based cohorts rather than
repeating the complete workflow one service at a time. A cohort may stage
several proxy, identity or DNS objects together only when they share a tested
pattern, recovery checkpoint, validation and rollback.

## Current state and evidence

- Authentik runs in LXC 106 at `192.168.50.22`; NPM runs in LXC 107 at
  `192.168.50.23`. Both monitored, backed up, mirrored, and covered by the
  encrypted off-site relay (`Backup-Architecture-Redesign.md`).
- `proxy.elliottrook.com` (NPM's own admin UI) — forward auth complete and
  tested, 2026-08-22.
- **Forgejo — native OIDC, complete and tested, 2026-08-31.** The one
  service actually onboarded so far. Confirmed via a full clean-session
  login (private window, no prior Authentik session) showing the complete
  password + passkey/MFA prompt. Two real bugs found and fixed during
  rollout (case-sensitive OAuth callback path; Forgejo's inability to parse
  JWE-encrypted tokens — see the Evidence log for full detail) plus one
  unrelated OPNsense inter-VLAN gap (Forgejo's host couldn't reach NPM at
  all) fixed with a single narrow pass rule.
- **Completed through 2026-09-15:** NPM, Forgejo, Homepage, Beszel, Grafana,
  the coordinated ARR stack, Portainer and both Pi-hole web interfaces have
  passed their real-login, denial, sign-out and recovery gates. Non-browser
  protocols and server-side widget/API paths remain direct.
- Full live dashboard inventory pulled 2026-09-10 (`/opt/homepage/config/services.yaml`)
  — ~35 apps total, most never previously scoped in this project. See Scope
  below and `docs/09-Service-Authorization-Onboarding.md`'s service plan
  table for the per-service detail.

## Scope and exclusions

**In scope:** the completed foundation and application packages above; the
remaining Milestone 3 browser interfaces (Immich, Seerr, Frigate, Code Server,
Dockge, Dozzle, Homarr, Newtarr, File Browser, NetBox, Calibre,
Audiobookshelf and Jellyfin); Milestone 4 infrastructure interfaces (Proxmox,
TrueNAS, both Synology systems, UniFi, Home Assistant and a separately decided
OPNsense browser path); and the explicitly defined Milestone 5 normalization,
regression, documentation and close-out work below.

**Plex scope correction:** Plex is assessment-only in this project. Retain
Plex authentication and every TV/mobile/remote-client path. Do not add an
Authentik enforcement layer unless a later, separately approved design proves
browser-only administration can be isolated without affecting clients.

**Frigate scope correction:** Frigate's browser UI is part of Milestone 3.
RTSP, ONVIF, camera discovery, recordings and integrations remain direct and
must never traverse Authentik.

**Milestone 3 packaging decision:** treat the operational *arr stack as one
coordinated work package, not five sequential service rollouts. Its fixed
membership is Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd, matching
`docs/ARR-Stack-Operational-Reference.md`. Design, approve, back up, implement,
validate and roll back that package behind one shared gate. Each browser UI may
still require its own hostname, NPM host and Authentik application, but those
are components of one atomic work package. Preserve every existing API-key
path among Prowlarr, the three ARR applications, SABnzbd, Homepage and the
automation tools; Authentik applies only to human browser access. The general
exception is limited to this already-completed atomic work package. For the
remaining targets, work is chunked by shared layer rather than by service:
discover/classify the whole cohort; capture one
verified cohort checkpoint; stage narrow network and NPM routes while DNS is
unpublished; create the matching Authentik applications/providers; publish the
cohort's DNS records together; then validate user workflows in risk-based
subcohorts. One failed member stops promotion of that member but does not
require rolling back already validated siblings. Native-OIDC application
configuration and any secret handoff remain per-application changes because
their rollback and credential risk are not shared.

**Never proxy through Authentik:** SSH, DNS, SMB, NFS, iSCSI, RTSP, ONVIF,
backup transports, the Ollama-compatible API, the Tailscale control path.
Confirmed additions from the full dashboard inventory: the AP Switch's raw
HTTP management page, Aster llama.cpp's inference API, GitHub (external,
own auth). Do not make firewall recovery depend on Authentik or the reverse
proxy.

**Excluded from autonomous execution:** human-only passkey/login/client tests,
new public ingress, changes beyond the narrow backend paths in the cohort
manifest, and the Standard's non-waivable stop conditions. Existing permitted
SSH transport and scoped firewall changes are covered by the Stream A approval.

## Authority model

- **Authentik** is authoritative for identity, groups, policy bindings and
  which users may reach which application.
- **NPM** is authoritative for the HTTPS routing/TLS layer in front of each
  service.
- **Each application** remains authoritative for its own users/roles where
  native OIDC is used (Authentik supplies identity, the app maps claims to
  its own roles).
- **This project document** is authoritative for rollout sequence,
  completion state and accepted risk. `docs/09-Service-Authorization-Onboarding.md`
  is authoritative for the technical how-to and the per-service completion
  record.
- **NetBox** is not authoritative for anything in this project; no DCIM
  facts change here.

## Architecture and data flows

```
Browser → https://home.elliottrook.com (NPM, 192.168.50.23)
            → forward-auth check → Authentik (192.168.50.22)
                → password + passkey
            → 302 back to NPM → proxied to Homepage (192.168.20.20:3000)

Browser → https://metrics.elliottrook.com (NPM)
            → native OIDC (if Beszel supports it) or forward auth
            → proxied to Beszel (192.168.20.20:8090)
```

Both target services stay on Servers VLAN 20; Authentik/NPM stay on
Management VLAN 50. The original design assumed no new cross-VLAN path was
required. **That assumption was disproved live on 2026-09-13:** an HTTP request
originating inside NPM LXC 107 to Homepage at `192.168.20.20:3000` timed out,
and the live OPNsense rules contain no matching pass rule. Existing reverse
proxy rules are service-specific (`192.168.50.23` to each backend and port),
so the least-privilege correction is one Homepage-only TCP rule from NPM
`192.168.50.23` to Docker LXC 100 `192.168.20.20:3000`. Beszel port 8090 is
not included and remains a later, separately approved change after Homepage
graduates.

For remaining cohorts, replace the example names above with the approved
cohort manifest. The trust flow stays the same: browser HTTPS terminates at
NPM; forward-auth checks go to Authentik while native-OIDC authorization goes
from the application to Authentik; NPM reaches only enumerated backend TCP
ports; application APIs, agents, storage, media streams and recovery paths stay
direct. Proxy and identity objects are staged before DNS makes a name normally
reachable.

## Privacy and security design

- Homepage forward auth gates the dashboard's browser UI only; its
  own widget calls to backend services (Portainer, Proxmox, TrueNAS, Sonarr,
  etc.) run server-side from the Homepage container itself and are
  unaffected by adding a login gate in front of the dashboard page.
- Beszel: if forward auth is used instead of native OIDC, its monitoring
  agents (on every other host) must keep using their existing private
  direct connection to the hub — never route agent-to-hub traffic through
  Authentik.
- Least privilege: until a deliberately designed household group replaces it,
  bind each remaining application directly to `jason`, matching the validated
  convention; never leave an application open to every Authentik identity.
- No credential, client secret or API key is committed to Git or intentionally
  printed. Safe inspection must explicitly exclude secret fields. The two
  accidental diagnostic exposures recorded in evidence were rotated and are
  included in Milestone 5's final secret review.

## Pre-start risk assessment

The first bullets below preserve the original Milestone 2 risk baseline and
its decisions. The 2026-09-15 addendum that follows governs the expanded
remaining cohorts.

- **Affected systems:** Homepage (Docker LXC 100), Beszel (same host),
  Authentik (LXC 106), NPM (LXC 107). No other guest is touched.
- **Users/data:** household users who use the Homepage dashboard daily;
  Beszel's monitoring data (metrics only, no secrets).
- **Current versions/dependencies (re-confirmed 2026-09-13):** Homepage's
  `latest` image is healthy; Beszel hub and co-located agent are `0.18.7` and
  healthy; Authentik is `2026.8.0`; NPM is healthy. Beszel `0.18.7` supports
  a custom OIDC provider with callback
  `https://metrics.elliottrook.com/api/oauth2-redirect`; password login stays
  enabled during rollout and agents retain their existing direct path.
- **Confidentiality/secret risk:** Authentik client secrets and any Beszel
  API credentials must be generated fresh, stored per this repo's existing
  pattern (protected recovery location, never Git), never printed to chat
  or logs.
- **Availability/integrity risk:** a forward-auth misconfiguration on
  Homepage could lock out the dashboard used to see the rest of the lab's
  health. Mitigation: NPM's direct-HTTP fallback (`192.168.20.20:3000`)
  stays live and untouched until the proxied path is fully validated;
  never remove the old path first.
- **Irreversible operations:** none required. Every step here (NPM proxy
  host, Authentik provider/application, DNS record) has a direct undo.
- **Firewall/DNS/cert changes expected:** a new DNS name
  (`home.elliottrook.com` / `metrics.elliottrook.com`) on both Pi-holes and
  OPNsense; the existing wildcard cert already covers `*.elliottrook.com`,
  no new cert needed. No firewall change is currently expected (see
  Architecture above) — if one turns out to be needed, that is a stop
  condition requiring Jason's explicit approval for that exact rule, same
  as every other OPNsense change in this repo, not a pre-authorized action.
- **Recovery checkpoint:** back up Authentik and NPM configuration before
  the first state-changing step (see Milestone 2).
- **Test strategy:** no synthetic/disposable target needed — both services
  already exist; testing is done against the real services with the direct
  URL kept live as the rollback path throughout.
- **Detection:** HomeLab Doctor already checks both services' direct
  reachability (`check_tcp` entries in `services.conf`); no new check is
  required to detect an outage, only to confirm the *proxied* path
  specifically works once live.
- **Resolved decision:** Beszel `0.18.7` supported native OIDC and graduated
  with password recovery retained; see Milestone 2 evidence.

### Remaining-wave risk addendum — 2026-09-15 redesign

- **Batch risk:** a malformed shared NPM, Authentik or DNS candidate could
  affect several staged names at once. Control: use an explicit cohort
  manifest, atomic database/configuration transactions where supported,
  unpublished DNS during proxy/identity staging, exact object-count checks and
  all-or-nothing rollback for the failed layer.
- **Availability:** forward-auth staging does not alter direct paths. Native
  OIDC activation can affect an application's login behavior, so those settings
  remain per-application changes with a tested local administrator and immediate
  rollback even though shared providers/proxies/DNS are batched.
- **Client compatibility:** Immich, Seerr, Frigate, Calibre, Audiobookshelf,
  Jellyfin and Home Assistant have non-browser consumers. Browser success alone
  cannot graduate them; mobile, TV, reader/player, API and integration paths are
  explicit workflow gates.
- **Privilege:** Code Server, Dockge, File Browser, NetBox and every Milestone 4
  interface can materially change infrastructure or data. Their cohort is
  staged together for efficiency but promoted only after deny tests, direct
  recovery and service-local role checks.
- **Credentials:** discovery must query only safe fields. Never clone or print
  client secrets, cookie secrets, API keys or mixed secret-bearing config.
  Secret handoff is source-to-target through protected mode-`0600` files and is
  validated by length/fingerprint or behavior, not value disclosure.
- **Rollback:** each cohort manifest maps every new firewall rule, NPM host,
  Authentik object, DNS record and application setting to its prior checkpoint.
  Removing one failed member must not delete shared objects used by a passed
  sibling. Direct private URLs remain the last-known-good path throughout.
- **Interruption:** expected outages are limited to controlled application or
  redundant-DNS restarts. The change stops if an unplanned service interruption,
  failed checkpoint, unexpected consumer, broader network path or credential
  exposure appears.

## Persistence plan

Per the new Standard's persistence requirements:

- This document and its Evidence log are the durable state. Before any
  state-changing step, the current milestone, next action and rollback
  location are recorded here — not held only in conversational memory.
- Continue in this session under Stream A; no scheduled job is created by
  inference. The historical sandbox findings are not current transport limits.
  Keep every layer resumable and stop safely on a platform denial.
- If this session stops (usage limit, interruption) mid-milestone: the next
  session re-reads this document, `docs/09-Service-Authorization-Onboarding.md`,
  and live state before continuing — never resumes from memory alone.
- The two now-defunct unattended-run artifacts (the disabled
  `authentik-rollout-homepage-beszel` scheduled task, and whatever state
  the two stalled sessions left behind) are recorded as closed below, not
  silently deleted.

## Milestones

### Milestone 0 — Close out the stalled unattended attempt (this redesign)

- [x] Diagnose the actual stall cause empirically (raw SSH denied to an
  allowlisted host even via an exact `permissions.allow` pattern) rather
  than assume.
- [x] Revert the sandbox-disabling change (`ee4c841`), confirmed live.
- [x] Disable the recurring scheduled task
  (`authentik-rollout-homepage-beszel`) so it cannot fire again under its
  old, now-superseded instructions.
- [x] Read `Project-Creation-Standard.md`, `docs/Standards.md` and
  `AGENTS.md`, and redesign this project document under the new template
  and Stream M.
- [ ] Confirm the two stalled sessions (`local_312ca3ad...`,
  `local_a30ead75...`) are actually stopped, not just no longer scheduled
  to recur — needs Jason to close them directly (not reachable from this
  session or the phone app; see prior conversation).

### Milestone 1 — Identity and policy foundation (retroactive verification)

The original Milestone 1 checklist was never checked off despite Forgejo
(Milestone 2) already succeeding — meaning the real prerequisites existed
in substance but were never confirmed in writing. Verify live before
Homepage/Beszel, don't assume Forgejo's success proves the foundation is
complete for a *different* service:

- [x] Confirm the actual current Authentik group(s) intended for Homepage/
  Beszel access (live query, not assumption). **Result, 2026-09-10: no
  `homelab-admins` group exists — that name was aspirational text only.**
  Real groups: `authentik Admins` (superuser), `authentik Agent-Users`,
  `authentik Read-only`. No consistent access-binding convention exists
  across current applications either: NPM, Synology, Synology Backup and
  Cloudflare Access are each bound to the individual user `jason`;
  Grafana is bound to the `authentik Admins` group; **Forgejo has no
  policy binding at all** (open to any authenticated Authentik identity —
  low practical risk today since only `jason`/`akadmin` exist, but not
  what this doc and the onboarding runbook describe as the intended
  design). Jason's decision for this pass: bind Homepage and Beszel to
  the user `jason` directly, matching the majority existing precedent.
- [x] Confirm at least two recoverable Authentik administrator methods
  still work (password + passkey, per the existing tested baseline).
  **Result, 2026-09-10:** `jason` has password + one WebAuthn device
  ("Apple Passwords"), both live, WebAuthn device last used the same day.
  `akadmin` (default break-glass admin) has password only, zero MFA
  devices — untested as a fallback path.
- [x] Back up Authentik and NPM configuration immediately before Milestone
  2's first state-changing step. **Completed 2026-09-13:** root-only
  application-consistent PostgreSQL/compose and SQLite/sanitized-inventory
  checkpoints were created under each service's protected local backup
  directory. `pg_restore -l` read the Authentik dump; SQLite
  `integrity_check` returned `ok`; hashes and sizes were recorded outside Git.

**Follow-ups surfaced by this live verification, out of scope for this
pass (per this project's own no-adjacent-tidying rule) — logged here so
they aren't lost, not actioned:**
- Forgejo's application has no access-policy binding. Fixing it is Milestone
  2 (Forgejo)-adjacent cleanup, not Homepage/Beszel work; needs its own
  small approved step later.
- Four Authentik applications exist that predate this document and were
  never recorded here: **Grafana, Synology, Synology Backup, Cloudflare
  Access.** Grafana and Synology are already anticipated in Milestones 3
  and 4 below, so their existing (non-standard) bindings should be
  reviewed when those milestones start rather than assumed correct.
  Cloudflare Access and Synology Backup aren't in this project's scope
  table at all yet.

### Milestone 2 — Homepage, then Beszel

Work one service at a time; do not start Beszel until Homepage is complete
and validated.

**Homepage:**
- [x] Confirm Homepage's current direct URL and credentials-free state
  (it has none today — first login será be through Authentik). **Re-confirmed
  2026-09-13:** direct HTTP returned 200 at `192.168.20.20:3000`; the running
  container is healthy.
- [x] Establish the least-privilege NPM-to-Homepage backend path after the
  preflight stop. **Completed 2026-09-13:** OPNsense rule
  `4accefaf-20b9-4537-9d0c-e7faf00e39a2` permits only TCP from
  `192.168.50.23` to `192.168.20.20:3000` on the Management interface. The
  loaded `pf` rule matched exactly and an HTTP request originating inside NPM
  returned 200. Beszel port 8090 remains excluded.
- [x] Create an NPM proxy host for `home.elliottrook.com` using the tested
  backup-first database/regeneration procedure required by this NPM release,
  matching `proxy.elliottrook.com`. **Completed 2026-09-13:** host ID 8 routes
  to `http://192.168.20.20:3000`, uses wildcard certificate 8, forced TLS,
  HTTP/2, WebSockets, exploit blocking and the minimal forward-auth block.
  Homepage's declarative allowed-host list now includes only the added friendly
  hostname; its prior Compose file is retained in a protected backup directory.
- [x] Create an Authentik Proxy Provider (forward-auth mode) + Application
  via Authentik's own API, bound to the confirmed identity from Milestone 1.
  **Completed 2026-09-13:** provider ID 15 uses `forward_single`, external
  host `https://home.elliottrook.com`, internal host
  `http://192.168.20.20:3000`, and the established authorization/invalidation
  flows. Application `homepage` has exactly one enabled binding to `jason`
  and the provider is attached once to the embedded outpost.
- [x] Add the DNS name to OPNsense and both Pi-holes. **Completed
  2026-09-14:** all three independently return `192.168.50.23`; the normal
  Mac resolver path also returns that address. Each resolver retains a
  protected pre-change checkpoint.
- [x] Validate: unauthenticated request → 302 to Authentik; complete
  password+passkey; land back on the friendly hostname; dashboard/widget
  requests still resolve correctly. **This step needs a human** (real
  browser, real login) — cannot be automated unattended regardless of the
  sandbox question. **Passed 2026-09-14:** fresh private Safari login used
  password + passkey and returned to Homepage; resource and service widget
  calls succeeded. The outpost sign-out endpoint ended the session and a
  revisit prompted for authentication. Authentik's policy engine independently
  evaluated `jason` as allowed and the non-owner `akadmin` as denied.
- [x] Confirm the direct URL (`192.168.20.20:3000`) still works unchanged.
  **Confirmed repeatedly through 2026-09-14:** direct HTTP returns 200 while
  the friendly unauthenticated path returns the expected Authentik 302.

**Beszel:**
- [x] Confirm the installed Beszel version's actual OIDC support (live
  check, not assumption) before choosing native OIDC vs. forward auth.
  **Result, 2026-09-13:** deployed `0.18.7` supports custom OIDC; use native
  OIDC with callback `https://metrics.elliottrook.com/api/oauth2-redirect`.
- [x] Confirm Beszel's actual current address (verify live; historically
  port 8090 on the same host, but verify rather than trust a historical
  reference). **Result, 2026-09-13:** direct HTTP returned 200 at
  `192.168.20.20:8090`; hub and co-located agent containers are healthy.
- [x] Establish the least-privilege NPM-to-Beszel backend path. **Preflight
  2026-09-14:** an HTTP request originating inside NPM to
  `192.168.20.20:8090` timed out, matching Homepage's earlier default-deny
  finding. The required rule is exactly TCP from `192.168.50.23` to
  `192.168.20.20:8090`; no agent path or other port is included. **Completed
  2026-09-14:** rule `58023f93-de8f-483d-8774-6bdbcb817297` passed persistent,
  loaded-state and source-local HTTP validation.
- [x] Establish Beszel's private HTTPS route and canonical URL. **Completed
  2026-09-14:** after validated application-consistent Beszel and NPM database
  checkpoints, changed only hub `APP_URL` to
  `https://metrics.elliottrook.com`, recreated only the hub, and created NPM
  host 9 to `192.168.20.20:8090` with certificate 8, forced TLS, HTTP/2,
  WebSockets and exploit blocking. No forward-auth block is present because
  Beszel will use native OIDC. All seven monitored systems returned `up` after
  the hub restart.
- [x] Publish `metrics.elliottrook.com` in private split DNS. **Completed
  2026-09-14:** OPNsense Unbound and both Pi-holes independently return
  `192.168.50.23`; the normal Mac resolver and certificate-valid HTTPS path
  pass. No public record or WAN ingress was created.
- [x] Same pattern as Homepage: NPM host + Authentik provider/application
  via their APIs, DNS, validate with a real login, confirm agents on every
  other host still reach the hub over their existing private path
  unaffected. **Completed 2026-09-14:** native OIDC uses a dedicated
  confidential Authentik provider, strict callback, PKCE, verified-email
  scope and direct `jason` binding. The first authorization exposed a missing
  `authorization_code` grant and the first account bootstrap exposed Beszel
  0.18.7's refusal to attach a new OAuth identity while user creation was
  disabled. Both were repaired without weakening the steady state: user
  creation was enabled only for the bound identity's first login, then
  disabled; the resulting link was atomically moved from the empty duplicate
  to the existing verified admin and the duplicate removed. A real iPhone
  Safari login returned to the admin dashboard with all seven systems, and
  sign-out returned to the page showing both password and Authentik login.
  Direct HTTP remains 200, password auth remains enabled, `akadmin` is denied,
  and all seven existing agents remain `up`.

### Gate

Both services reachable through friendly HTTPS names with tested
sign-in/sign-out/denial/direct-fallback, and losing Authentik/NPM does not
prevent direct administrative recovery of either.

**Passed 2026-09-14.** Homepage and Beszel meet every Milestone 2 condition;
the 2026-09-15 observation pass found no regression.

### Milestone 3 — Operations/application wave

Completed packages below retain their evidence. Remaining work follows the
layer-based cohort design later in this milestone; it does not repeat an
end-to-end rollout one service at a time.

**Grafana:**
- [x] Observe Milestone 2 before starting the next service. **Passed
  2026-09-15:** Homepage direct/protected behavior remained 200/302, Beszel
  direct/HTTPS remained 200, all seven systems stayed `up`, its OAuth link
  remained on the verified admin, password fallback stayed enabled, all three
  resolvers agreed, NPM syntax passed, and Forgejo/GitHub refs matched.
- [x] Audit the existing Grafana HTTPS, NPM, DNS, Authentik and local-admin
  state. The hostname, proxy, wildcard certificate, three private DNS records,
  canonical `root_url`, strict callback and confidential provider were already
  correct; Generic OAuth was disabled and one local server administrator
  remained available.
- [x] Back up Authentik and Grafana immediately before activation. The
  Authentik PostgreSQL dump/Compose checkpoint and Grafana online SQLite/INI
  checkpoint are protected locally; `pg_restore -l` and SQLite
  `integrity_check` passed.
- [x] Enable native OIDC while retaining local login. Grafana now uses the
  existing provider with authorization-code flow, PKCE, OpenID/profile/email
  scopes and group-derived organization Admin role. The former two-member
  `authentik Admins` application binding was replaced with the established
  direct `jason` binding; Grafana's local login form and active local server
  admin remain intact.
- [x] Validate real login, dashboard access, sign-out, denial and fallback.
  A private iPhone Safari login completed password/passkey authentication and
  reached the provisioned HomeLab overview as the existing organization Admin.
  Grafana sign-out returned to the page containing local and Authentik login.
  Authentik policy evaluation allows `jason` and denies `akadmin`; direct login
  remains HTTP 200. The first login exposed an invalid constant role expression
  and was corrected to Grafana's supported group-based expression before the
  successful retest.

**Portainer — completed package:**
- [x] Audit the live service and access path. Portainer CE `2.39.5` is healthy
  in Docker LXC 100 with direct HTTP `:9000` and HTTPS `:9443` recovery paths,
  internal authentication and a Docker-socket mount. NPM cannot currently
  reach either port; no Portainer NPM host, split-DNS record or Authentik
  application exists.
- [x] Capture the immediate recovery checkpoint. A consistent stopped-container
  archive of Portainer's data volume plus container metadata, fresh Authentik
  PostgreSQL/Compose and NPM SQLite checkpoints, OPNsense XML, both Pi-hole
  configurations and Homepage services configuration are protected locally.
- [x] Open only the selected NPM-to-Portainer backend path. One logged TCP rule
  permits NPM `192.168.50.23` to `192.168.20.20:9000`; Portainer's direct HTTPS
  port 9443 remains blocked from NPM and available from the trusted client path.
- [x] Create and validate the private HTTPS route before DNS publication. NPM
  host 15 forwards HTTPS `portainer.elliottrook.com` to private HTTP port 9000
  with wildcard certificate 8, forced TLS, HTTP/2, WebSockets and exploit
  blocking; pinned-host root, Origin-header and status checks return 200.
- [x] Configure dedicated native OAuth/OIDC while retaining the initial local
  administrator as break-glass. The owner-only Authentik application maps
  `jason` to existing Portainer user `admin` through a dedicated claim; automatic
  user creation is disabled. Portainer accepted its friendly Origin without a
  trusted-origin container change.
- [x] Publish three-resolver split DNS. OPNsense and both Pi-holes resolve
  `portainer.elliottrook.com` to NPM; normal root and Origin-header API requests
  return 200 and both Pi-holes are healthy.
- [x] Test real private-session login/sign-out,
  non-owner denial, local recovery and the existing Homepage API widget, then
  change only the tile link. Jason completed native OAuth from Private Safari,
  Portainer returned to the existing `admin` account, logout required a fresh
  Authentik authentication, and the direct HTTPS local-admin path remained
  usable. The Homepage API token still returns 200; only the tile `href` now
  uses `https://portainer.elliottrook.com` while its widget URL remains direct.

**Pi-hole primary and secondary — coordinated package:**
- [x] Audit both live services and their access paths. Primary Pi-hole
  `2026.05.0` is healthy in Docker LXC 100 at `192.168.20.20:8082`; secondary
  Pi-hole `2026.07.2` is running as a TrueNAS App at
  `192.168.20.40:20720`. Their DNS listeners on TCP/UDP 53 remain explicitly
  outside the proxy design. Neither proposed friendly name exists yet, and
  NPM cannot reach either web backend through the current firewall policy.
- [x] Capture the immediate recovery checkpoint. Fresh root-only Authentik
  PostgreSQL/Compose, NPM SQLite, OPNsense XML, both Pi-hole configurations,
  the TrueNAS application configuration and Homepage services configuration
  are stored in protected local backup directories with recorded hashes.
- [x] Open exactly two NPM-to-web-UI paths, one to each existing HTTP port;
  do not expose or alter DNS port 53. Logged TCP rules permit only NPM
  `192.168.50.23` to primary `192.168.20.20:8082` and secondary
  `192.168.20.40:20720`; both paths now answer from inside NPM.
- [x] Set each Pi-hole v6 `webserver.domain` through the validated FTL CLI so
  its future friendly Host header is accepted. Changes were applied one at a
  time; both containers, DNS authorities and direct-IP recovery paths remained
  healthy, and each friendly Host preflight changed from 403 to the expected
  root-to-`/admin/` redirect.
- [x] Create `dns1.elliottrook.com` and `dns2.elliottrook.com` as staged private
  NPM hosts with dedicated Authentik forward-auth applications and owner-only
  bindings. Providers 23-24 have complete strict callbacks, mappings and grants;
  NPM hosts 16-17 pass certificate-valid pinned tests and reach Authentik's
  login flow. OPNsense Unbound and both Pi-holes now publish both private names
  to NPM, and normal certificate-valid requests return their same-host
  Authentik start routes.
- [x] Test both interfaces from a fresh private session, confirm SSO and
  sign-out, retain direct recovery and DNS service, then change only the two
  Homepage tile links. Keep the primary widget URL and file-backed credential
  direct. Jason completed Authentik and the retained primary Pi-hole login,
  reached both dashboards through one SSO session, and confirmed sign-out
  required Authentik again. Only the two tile `href` values now use friendly
  HTTPS; the primary widget still uses its direct v6 API and returns 200.

#### Remaining Milestone 3 cohort design

The remaining application wave is divided by blast radius and workflow, not
into twelve repeated end-to-end service projects:

- **Cohort 3A — bounded browser gates:** Dozzle, Homarr, Frigate browser UI and
  Newtarr after discovery establishes what it is and who consumes it. These are
  expected to use forward auth. Frigate's streams/integrations remain direct.
- **Cohort 3B — administrator-capable interfaces:** Code Server, Dockge, File
  Browser and NetBox. Treat the whole cohort as privileged even where an
  interface is read-only; retain local recovery and validate denied-user
  behavior before publishing Homepage links.
- **Cohort 3C — client-sensitive media applications:** Immich, Seerr, Calibre,
  Audiobookshelf and Jellyfin. Prefer supported native OIDC, but configure each
  application's OAuth secret/role mapping separately. Mobile, TV, reader,
  player, callback and API behavior must pass before enforcement. Plex is not a
  member; it remains assessment-only with no authentication change.

Each cohort uses the following layer gates. Under Stream A, record the exact
object inventory and rollback before executing each bounded layer:

- [ ] **Discovery and classification:** record versions, direct URLs, owners,
  existing authentication, API/mobile/automation consumers, hostname/Host
  requirements and whether native OIDC is genuinely supported. Unknown or
  materially different members leave the cohort before mutation.
- [ ] **Cohort recovery checkpoint:** capture and verify Authentik, NPM,
  OPNsense, all three DNS configurations, Homepage and every member's relevant
  configuration/database. Do not proceed if any required checkpoint fails.
- [ ] **Network and proxy staging:** add only the enumerated NPM-to-backend TCP
  paths and create all cohort NPM hosts against the wildcard certificate while
  DNS remains unpublished. Validate every backend, certificate, Host header,
  NPM database and generated configuration in one gate.
- [ ] **Identity-object batch:** atomically create the cohort's forward-auth or
  native-OIDC providers/applications, strict callbacks, standard mappings and
  direct `jason` bindings. Validate `jason` allow/`akadmin` deny and outpost
  membership without printing credentials. Application-side native OIDC and
  secret transfer remain individually checkpointed and validated substeps.
- [ ] **DNS publication batch:** add the entire validated cohort to OPNsense and
  both Pi-holes in one reviewed candidate, reload redundant resolvers safely,
  and prove every name independently on all three authorities.
- [ ] **Workflow promotion:** test real private-session login, SSO, sign-out,
  direct recovery, non-browser consumers and service-specific clients. Promote
  Homepage links only for members that pass; leave failed members staged and
  unpublished from Homepage with an explicit blocker and rollback decision.

Durable cohort status (update cells only from evidence, not intent):

| Cohort | Discovery | Checkpoint | Network/proxy | Identity objects | DNS | Workflow/promotion |
|---|---|---|---|---|---|---|
| 3A — bounded browser gates | Dozzle/Homarr verified; Newtarr/Frigate held | Dozzle/Homarr passed | Dozzle/Homarr passed | Dozzle/Homarr passed | Dozzle/Homarr passed | Human tests pending; links unchanged |
| 3B — administrator interfaces | Four browser backends classified | Passed | Passed | Passed | Passed on all three resolvers | Human tests pending; links unchanged |
| 3C — client-sensitive media | Pending | Pending | Pending | Pending | Pending | Pending |

Milestone 3 completes when Cohorts 3A-3C pass, Plex's no-change assessment is
recorded, and all previously completed Milestone 3 packages remain healthy.

### Milestone 4 — Infrastructure-interface cohorts

Infrastructure work uses the same layer batching but a higher recovery bar:

- **Cohort 4A — native identity platforms:** Proxmox, TrueNAS and the main
  Synology interface. Backup Synology was retired on 2026-09-22 and is no
  longer an onboarding target; its stale objects require reviewed cleanup.
  Batch shared discovery/checkpoints, proxy
  staging, Authentik objects and DNS; activate native identity and map roles per
  platform. Preserve `root@pam`, TrueNAS local administration and main Synology
  local recovery paths. SMB, NFS, iSCSI, backup and hypervisor traffic remain
  direct.
- **Cohort 4B — household/control planes:** UniFi and Home Assistant. Batch
  proxy/DNS/identity staging, but validate Home Assistant browser, companion
  app, callbacks and emergency access separately before enforcement. Preserve
  UniFi local console/direct recovery.
- **OPNsense decision gate:** default is no proxy or Authentik dependency for
  the firewall UI. `firewall.elliottrook.com` is created only after a separate
  risk decision proves that LAN/Tailscale direct recovery cannot be impaired.

- [ ] Complete Cohort 4A through the six layer gates used by Milestone 3.
- [ ] Complete Cohort 4B through the six layer gates used by Milestone 3.
- [ ] Record and implement the OPNsense decision (approved recovery-safe design
  or explicit no-change conclusion).
- [ ] Run an infrastructure-wide recovery test with Authentik/NPM unavailable
  by reasoned path validation or controlled interruption, without risking the
  last firewall/hypervisor/storage administration path.

### Milestone 5 — Policy normalization, integration and graduation

Milestone 5 is now explicit; it is not another service-onboarding wave:

- [x] Add the missing owner-only Forgejo application policy binding and verify
  `jason` allow/`akadmin` deny without changing Forgejo's working native OIDC.
- [ ] Inventory Synology Backup and Cloudflare Access, then either bring their
  bindings/documentation into the project standard or record a deliberate
  exclusion with owner and rationale.
- [ ] Confirm the two stale pre-redesign sessions are stopped or archived and
  record the human verification; remove no current task or automation by
  inference.
- [ ] Run the full regression matrix: every friendly route, direct recovery
  path, Authentik denial, sign-out, widget/API/agent/mobile/client path, three
  DNS authorities, NPM integrity/syntax and narrow loaded firewall rules.
- [ ] Review secrets and temporary files without printing values; confirm all
  credentials are protected, all accidental disclosures were rotated, and no
  temporary access remains.
- [ ] Finish the integration checklist: Doctor/monitoring decision, backup and
  restore order, human wiki, Aster mirror, operational reference, onboarding
  completion table, portfolio, architecture/addressing and Homepage.
- [ ] Perform a proportional restore/rebuild proof for Authentik/NPM and one
  representative native-OIDC and forward-auth service path.
- [ ] Record accepted limitations, move the project to completed projects,
  update all links, create the focused close-out commit, push Forgejo with
  immediate approval and verify the GitHub mirror.

## Validation and evaluation

- Functional: login succeeds with the correct account, fails for a denied
  account, sign-out actually ends the session.
- Regression: existing Forgejo/NPM-admin integrations still work after any
  change here (shared Authentik/NPM instance).
- Failure-mode: confirm the direct URL still works if Authentik is
  unreachable (stop Authentik briefly in a controlled test, or reason from
  the already-proven NPM/Forgejo pattern rather than repeat a disruptive
  test if the mechanism is identical).
- Two independent passes are not required here (this is not AI-mediated
  production behavior in the sense the Standard reserves that for) but the
  login test should be run from a genuinely fresh/private session, not a
  cached one, matching this project's own established practice.

## Observability and maintenance

- HomeLab Doctor already checks both services' direct TCP reachability;
  no change needed there.
- Consider (not required for graduation): a Doctor check for the *proxied*
  path specifically, mirroring how Forgejo's onboarding did not add one —
  matching existing practice, not a new gap unique to this milestone.

## Backup, restore and rollback

- Authentik and NPM configuration backed up before the first state change
  (Milestone 1).
- Rollback for any step here is direct: delete the NPM proxy host and/or
  Authentik provider/application; the service's direct URL was never
  removed, so no outage results.
- Homepage's Compose checkpoint and Beszel's Compose plus online SQLite
  checkpoints cover their canonical-host/OIDC changes. Beszel also has an
  integrity-checked checkpoint immediately before the guarded OAuth-link
  repair. These are rollback checkpoints rather than new recurring jobs; the
  existing service backup regime remains unchanged.

## Documentation and systems-of-record updates

- [x] **HomeLab Doctor** — not applicable; existing checks already cover
  direct reachability.
- [x] **Backup and recovery** — immediate validated checkpoints were captured
  for Authentik, NPM, Homepage, Beszel and each changed resolver/firewall layer.
- [x] **NetBox** — not applicable; no device/IP/VLAN fact changes.
- [x] **Authentication/authorization** — this project *is* the change;
  update `docs/09-Service-Authorization-Onboarding.md`'s completion record
  for each service as it's validated.
- [x] **DNS, certificates and firewall** — record the two new DNS names
  added; no new certificate needed (existing wildcard).
- [x] **Homepage/service discovery** — Homepage has no self-tile; Beszel's
  clickable `href` now uses `https://metrics.elliottrook.com`, while its
  server-side widget correctly retains the direct private URL.
- [x] **Repository documentation** — update this project's status and the
  portfolio (`docs/projects/README.md`) at each milestone gate.

## Graduation criteria

Milestone 2 graduated when Homepage and Beszel became live on friendly
HTTPS names, validated end-to-end by a real login, direct fallback proven,
and the onboarding completion record was updated for both. The whole project
graduates only after all remaining Milestone 3 cohorts, Milestone 4 cohorts
and the now-explicit Milestone 5 close-out gates pass. Cohort batching changes
delivery efficiency, not the requirement for per-service recovery and workflow
evidence.

## Evidence log

| Date | Item | Evidence | Result |
|---|---|---|---|
| 2026-09-23 | Stream A transition and recovery checkpoints | Jason approved the proposed backups and moved the remainder to Stream A. Protected shared/member/resolver checkpoints were validated; source-local paths are recorded above. | Stream A active; platform controls, human workflow gates and immediate remote Git write approval remain. |
| 2026-09-23 | Six additional private browser routes | Staged Dozzle, Homarr, Code Server, Dockge, File Browser and NetBox with exact NPM-source TCP rules, six owner-only applications, wildcard TLS and three-resolver DNS. Loaded rules, all eighteen DNS answers, Authentik flows, allow/deny policy checks and spoofed-header denial pass. | Awaiting real login, account/role, sign-out and recovery acceptance; Homepage links unchanged. Newtarr and Frigate remain held as described above. |
| 2026-09-23 | Forgejo policy normalization | Added only binding `7999395c-3923-41cc-9010-856996dacef5` to existing application/provider 9. | Owner allowed, non-owner denied; native OIDC provider untouched and HTTPS root remains 200. |
| 2026-09-23 | Database recovery proof | Restored a fresh Authentik dump into a disposable database and verified native/forward-auth application rows, then removed it. Reopened fresh NPM backup with integrity `ok` and all six hosts. | Passed database recovery proof; full service rebuild and human workflow gates remain open. |
| 2026-08-22 | Nginx Proxy Manager | Authentik forward auth with password and passkey | Passed |
| 2026-08-24 | Project split | Rollout separated from initial-build record | Complete |
| 2026-08-25 | Authentik launch URL follow-up | Verified Base URL/outpost/NPM headers; replaced dashboard HTTP fallback link with `https://auth.elliottrook.com` | Passed |
| 2026-08-31 | Forgejo | Native OIDC via a dedicated Authentik OAuth2/OpenID Provider. Two real bugs found and fixed: (1) case-sensitive OAuth callback path mismatch, found by capturing the live `authorize` request rather than guessing; (2) Forgejo's inability to parse JWE-encrypted tokens, fixed by clearing the provider's Encryption Key. A missing OPNsense inter-VLAN rule (Forgejo's host to NPM) was also found and fixed with one narrow pass rule. Validated with a full clean-session login showing the complete password + passkey/MFA prompt. | Passed |
| 2026-09-09/10 | Unattended attempt (superseded) | Granted a per-project authorization for an unattended scheduled task covering Homepage/Beszel, later widened for a narrow OPNsense case, then further widened in scope to the full dashboard inventory (Milestone 3 planning only, never executed). The task stalled ~11 hours with zero configuration progress, then unilaterally disabled the repo's Bash sandbox to work around a real but out-of-scope blocker instead of stopping to ask | Superseded by this redesign. No Authentik/NPM configuration was ever actually changed during the entire unattended attempt — the stall happened before any state-changing step |
| 2026-09-10 | Sandbox incident | Empirically confirmed raw SSH is denied to allowlisted hosts even for exact `permissions.allow` patterns (`ssh truenas cat /etc/hostname` → `Operation not permitted`), confirming the stalled session's diagnosis was technically correct even though its fix was not. Reverted the sandbox-disable commit (`ee4c841`), confirmed live. Disabled the recurring scheduled task | Sandbox restored; task disabled; root cause understood and documented rather than worked around by weakening a platform control |
| 2026-09-10 | Redesign | Project taken back under `Project-Creation-Standard.md`, Stream M selected (the remaining work genuinely needs a human for live login validation and cannot safely run fully unattended given the confirmed SSH/sandbox constraint), workaround adopted (prefer each application's own HTTPS API over SSH for every configuration step, since HTTPS to allowlisted hosts already works cleanly through the sandbox) | This document restructured to the new 17-section template; Milestone 0 (close-out) mostly complete, Milestone 1 reopened for live re-verification, Milestone 2 reset to not-started (no real progress was lost, since none had been made) |
| 2026-09-10 | Sandbox finding #2: IP-only allowlist entries don't work for HTTP(S) either | Confirmed empirically: `https://github.com` and `https://git.elliottrook.com` (hostname allowlist entries) returned `200`; the same requests against the literal IPs `192.168.50.22`/`192.168.50.23` (also allowlisted, per `CLAUDE.md`'s table) failed instantly with `Operation not permitted` on every port tried (80, 81, 443, 9000, 9443). The sandbox's HTTP(S) proxy filters by hostname, not IP — this is broader than the SSH/raw-TCP finding from the redesign above, and likely means most of the CLAUDE.md sandbox table has never actually worked for HTTP(S) from a sandboxed session either, only for tooling that bypasses this proxy | Fixed with Jason's explicit approval: added `auth.elliottrook.com` and `proxy.elliottrook.com` as hostname entries to `.claude/settings.json`'s `allowedDomains` (additive only, existing IP entries untouched); CLAUDE.md's sandbox table updated in the same change |
| 2026-09-10 | Permission-gate friction (separate from the sandbox) | Even with the hostname fix, ad hoc `curl` calls kept triggering Bash permission prompts — `.claude/settings.json`'s `permissions.allow` had no `curl` entry at all (only `cat`/`ls`/`ping`/per-host read-only `ssh`). Resolved by adding `scripts/api-get.sh`, a wrapper that only ever issues a GET (hard-rejects `-X`/`-d`/`-F`/`-T`/`-u`) against `auth.elliottrook.com/api/*` or `proxy.elliottrook.com/api/*`, allow-listed as `Bash(scripts/api-get.sh:*)` — narrower than a general curl allow, same philosophy as the existing per-host `ssh ... cat:*` patterns. A second, separate friction source was also found and worked around: any Bash command containing shell variable expansion (e.g. `"$TMPDIR"`) is flagged "cannot be statically analyzed" and always prompts regardless of allow-list matches — worked around by using literal paths/values in command text instead of `$VAR` expansion | `scripts/api-get.sh` is now the standing pattern for read-only Authentik/NPM API discovery in this and future sessions |
| 2026-09-10 | Milestone 1 live verification | Queried Authentik's API read-only via the new wrapper: groups, users, authenticator devices, applications, and policy bindings. See Milestone 1 checklist above for full results (no `homelab-admins` group exists; inconsistent access-binding convention across existing apps; Forgejo has no policy binding; `jason` has password+passkey, `akadmin` has password only; four undocumented pre-existing applications found: Grafana, Synology, Synology Backup, Cloudflare Access) | Milestone 1's first two checklist items confirmed live; third (backup) deferred to immediately before Milestone 2's first state-changing step per its own wording; follow-ups logged in the Milestone 1 section rather than actioned, per this project's scope rule |
| 2026-09-13 | Resume audit before Milestone 2 | Clean Git worktree at `33437d0`, with both configured remotes at the same commit. Direct Homepage and Beszel HTTP paths returned 200; running containers reported healthy, with Beszel hub/agent at `0.18.7`. NPM's live host inventory contains neither intended hostname. Authentik `2026.8.0` contains neither target application/provider; existing groups and owner-binding convention remain as recorded, and the embedded outpost still advertises `https://auth.elliottrook.com`. OPNsense and both Pi-holes returned no A record for either target hostname. Daily LXC archives for 106/107 dated 2026-09-13 exist, but these do not replace the required immediate application-consistent checkpoint. | No partial rollout or surprise topology found. Actual next gate is the monitored, pre-change Authentik PostgreSQL/compose and NPM SQLite/API backup. Homepage remains first; Beszel native OIDC follows only after Homepage passes its complete gate. |
| 2026-09-13 | Milestone 1 pre-change backup | With explicit Stream-M approval, created root-only Authentik PostgreSQL custom dump plus compose checkpoint and an NPM SQLite online-backup plus sanitized proxy-host inventory in each service's protected local backup directory. The Authentik dump was enumerated successfully with `pg_restore -l`; NPM SQLite returned `integrity_check=ok` with seven active proxy hosts; all files were non-empty, mode `0600`, inside mode `0700` directories, and had SHA-256 hashes recorded outside Git. Direct Homepage/Beszel remained HTTP 200; Authentik and protected NPM paths retained their expected HTTP 302 responses. | Passed. Milestone 1 is complete; next action is the first bounded Homepage layer, after a fresh exact Stream-M approval. |
| 2026-09-13 | Homepage network preflight stop | From inside NPM LXC 107, an HTTP connection to `192.168.20.20:3000` timed out. Read-only OPNsense inspection showed service-specific NPM-to-backend rules for Synology, Grafana, Forgejo and the Aster wiki, but none for Homepage. Homepage itself remained directly healthy from the trusted client path. | The documented no-firewall-change assumption was false, so no proxy or identity object was created. Next action requires a fresh Stream-M approval for exactly one TCP pass rule from NPM `192.168.50.23` to Homepage `192.168.20.20:3000`, with a pre-change OPNsense backup and rollback by removing only that rule. |
| 2026-09-13 | Homepage private network gate | With explicit Stream-M approval, saved root-only OPNsense checkpoint `/conf/backup/config-authentik-homepage-before-20260913.xml`, then added model-backed rule `4accefaf-20b9-4537-9d0c-e7faf00e39a2` and reloaded the filter. Persistent and loaded state permit exactly TCP `192.168.50.23` to `192.168.20.20:3000` on Management VLAN 50. A request originating inside NPM returned HTTP 200; direct Homepage and Beszel paths also remained HTTP 200. | Passed. No Beszel port or broader network was opened. Next Homepage layer is the dedicated Authentik forward-single provider/application, owner binding and embedded-outpost attachment after separate approval. |
| 2026-09-13 | Homepage Authentik identity gate | With explicit Stream-M approval, an atomic transaction created proxy provider ID 15 (`forward_single`, external `https://home.elliottrook.com`, internal `http://192.168.20.20:3000`), application `homepage`, exactly one enabled direct binding to `jason`, and one embedded-outpost attachment. The first attempt rejected the obsolete UUID form for `PolicyBinding.target` and rolled back completely; the corrected transaction used the application object and committed cleanly. Read-back confirmed both established flows and `authentik_host=https://auth.elliottrook.com`; existing applications were unchanged and Authentik/NPM regressions retained their expected 302 responses. | Passed. No credential or client secret was created. The next layer is Homepage's allowed-host declaration plus NPM host creation, after separate approval. |
| 2026-09-13 | Homepage reverse-proxy gate | With explicit Stream-M approval, saved Homepage's Compose file in its mode-0700 protected backup directory, appended only `home.elliottrook.com` to `HOMEPAGE_ALLOWED_HOSTS`, and recreated only the Homepage container. After its brief health-starting interval it returned healthy and accepted both direct and friendly Host requests. Created NPM proxy host 8 from the known-good host-2 pattern, pointing to `192.168.20.20:3000` with certificate 8, forced TLS, HTTP/2, WebSockets, exploit blocking and minimal Authentik forward auth. NPM regenerated all enabled hosts successfully; `nginx -t` passed. Generated host 8 contains the auth-request/outpost locations and no `X-authentik-*` propagation. Certificate-valid `curl --resolve` returned HTTP/2 302 to the same friendly hostname's Authentik start path; direct Homepage stayed HTTP 200 and existing Authentik/NPM endpoints retained HTTP 302. | Passed. DNS remains deliberately unpublished, so ordinary clients are not cut over. Next action is the three-resolver split-DNS publication after separate approval. |
| 2026-09-14 | Homepage split-DNS gate | With explicit Stream-M approval, saved protected pre-change copies of OPNsense `config.xml` and each Pi-hole's `pihole.toml`; added only `home.elliottrook.com -> 192.168.50.23` to OPNsense Unbound and both Pi-hole `dns.hosts` arrays. OPNsense model validation and `unbound check` passed before restart. The Pi-hole `pihole reloaddns` wrapper emitted a version-specific readonly-variable error on one invocation, but direct follow-up proved both running FTL processes had already loaded the record and both containers remained healthy. OPNsense and both Pi-holes independently returned the intended address; the Mac's normal resolver did too after its earlier negative cache expired. Normal HTTPS returned the correct same-host Authentik 302. | Passed without public DNS or WAN exposure. NPM syntax, direct Homepage and existing protected-host regressions remained healthy. |
| 2026-09-14 | Homepage interactive authentication | Jason opened the friendly hostname from a fresh private Safari session on iPhone and completed Authentik password plus passkey. A fresh Authentik login and application-authorization event appeared at the same time, followed by successful Homepage resource and service-proxy requests through NPM, including live widget traffic; the browser returned to `home.elliottrook.com`. The outpost sign-out endpoint ended the session and revisiting Homepage prompted for login. Authentik's own uncached policy-engine evaluation returned allow for bound owner `jason` and deny for non-owner `akadmin`. Independent unauthenticated probing still returns the expected 302, and direct fallback remains HTTP 200. | Homepage passed sign-in, sign-out, same-host return, explicit authorization denial, dashboard/widget behavior and direct recovery. No Homepage self-tile exists; the Beszel tile remains deliberately direct until Beszel graduates. Homepage is complete and Beszel is now the next service. |
| 2026-09-14 | Beszel network preflight stop | Direct Beszel remained healthy at `192.168.20.20:8090`, but an HTTP request originating inside NPM timed out. This confirms the same service-specific OPNsense default-deny boundary encountered for Homepage; the existing agent-to-hub paths are unrelated and remain unchanged. | No Beszel configuration was changed. Next action requires separate Stream-M approval for one TCP rule from NPM `192.168.50.23` to Beszel hub `192.168.20.20:8090`, with a fresh OPNsense checkpoint and targeted rollback. |
| 2026-09-14 | Beszel private network gate | With explicit Stream-M approval, saved root-only OPNsense checkpoint `/conf/backup/config-authentik-beszel-before-20260914.xml`, added model-backed rule `58023f93-de8f-483d-8774-6bdbcb817297`, and reloaded the filter. Persistent and loaded state permit exactly TCP `192.168.50.23` to `192.168.20.20:8090` on Management VLAN 50. An HTTP request originating inside NPM returned 200; direct Beszel and Homepage remained HTTP 200, protected Homepage retained HTTP 302, and Beszel hub/agent stayed running. | Passed. No existing agent path or other port was changed. Next layer is Beszel's private TLS NPM host and canonical `APP_URL`, after separate approval. |
| 2026-09-14 | Beszel private HTTPS gate | With explicit Stream-M approval, created a root-only online backup of Beszel's live SQLite database plus its Compose file and a fresh NPM online SQLite backup. Both database `integrity_check` operations returned `ok`; hashes and sizes were recorded outside Git. Changed only Beszel hub `APP_URL` from its direct HTTP address to `https://metrics.elliottrook.com`, recreated only the hub, and created NPM host 9 pointing to `192.168.20.20:8090` with wildcard certificate 8, forced TLS, HTTP/2, WebSockets and exploit blocking. The host has no forward-auth configuration because Beszel will use native OIDC. `nginx -t` passed and certificate-valid `curl --resolve` returned HTTP/2 200 from the friendly name. The co-located agent reconnected ten seconds after the hub restart; the live Beszel database reported all seven systems `up`. Direct Beszel remained HTTP 200 and protected Homepage retained its expected 302. | Passed. DNS remains unpublished, existing password login remains enabled, and no OAuth secret exists yet. Next action is three-resolver private DNS publication after separate approval. |
| 2026-09-14 | Beszel split-DNS gate | With explicit Stream-M approval, saved protected pre-change copies of OPNsense `config.xml` and both Pi-hole `pihole.toml` files; added only `metrics.elliottrook.com -> 192.168.50.23` to OPNsense Unbound and both Pi-hole `dns.hosts` arrays. OPNsense model validation and `unbound check` passed before restart. All three resolvers and the Mac's normal resolver independently returned the intended address; certificate-valid HTTPS returned Beszel HTTP 200. Both Pi-holes, Beszel hub, co-located agent and Homepage remained running/healthy, all seven Beszel systems remained `up`, NPM syntax passed, direct Beszel remained HTTP 200 and protected Homepage retained HTTP 302. | Passed without public DNS or WAN exposure. Beszel still uses its existing password login. Next action is the dedicated Authentik OAuth2/OIDC provider plus Beszel custom-provider configuration after separate approval. |
| 2026-09-14 | Beszel native OIDC and interactive gate | With explicit Stream-M approvals, created dedicated Authentik OAuth2 provider 16/application `beszel`, strict authorization callback, PKCE-capable confidential client, custom verified-email scope and one direct `jason` binding; configured Beszel's PocketBase users collection with that provider while retaining password authentication and default-disabled user creation. Live testing found and corrected an omitted `authorization_code` grant. Beszel 0.18.7 then refused the first unlinked identity with `Only superusers can perform this action`; user creation was temporarily enabled behind the existing single-user Authentik binding for one bootstrap login and immediately disabled. That produced an empty duplicate account, so a fresh integrity-checked backup was taken and a guarded SQLite transaction moved the sole external-auth link to the pre-existing verified admin and deleted only the duplicate. | Passed. A real iPhone Safari login reached the original admin dashboard with all seven systems; sign-out returned to the login page with password and Authentik choices. Read-back shows one OAuth link on the verified admin, two original users, no duplicate, user creation disabled, password authentication enabled, all seven agents `up`, direct and HTTPS paths HTTP 200, and policy allow/deny for `jason`/`akadmin`. Temporary credential and repair files were removed from every transfer hop. |
| 2026-09-14 | Milestone 2 service discovery and graduation | Changed only Homepage's live Beszel tile `href` to `https://metrics.elliottrook.com`; retained the widget's direct `http://192.168.20.20:8090` endpoint and file-backed credentials. Homepage direct rendering and Beszel widget endpoint both returned 200. Updated the service-onboarding completion record, addressing/network facts and portfolio status. | Milestone 2 complete. Homepage and Beszel are live on private friendly HTTPS names with real sign-in/sign-out, explicit denial, direct recovery and non-browser/agent behavior validated. Milestones 3–5 remain not started. |
| 2026-09-14 | Milestone 2 Git synchronization | Created focused local commit `5776699` and, with explicit approval, pushed it to authoritative Forgejo `origin/main`. Forgejo's configured mirror advanced GitHub `main` to the identical full commit without a direct GitHub push. The repository directive and Project Creation Standard were corrected to make this single-push topology explicit. | Passed: Forgejo and GitHub both reported `577669981db0e2ea075c41cc0515444a43cc8025`; direct duplicate pushes to GitHub are no longer part of routine milestone close-out. |
| 2026-09-14 | Milestone 3 ARR packaging decision | Jason directed that Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd be handled as one coordinated work package rather than sequential rollouts. The project scope and onboarding plan now define one shared design/approval/backup/validation/rollback gate while preserving all API-key integrations and limiting Authentik to browser UI access. | Design updated; no Milestone 3 live change started. The one-service-at-a-time rule remains in force for every non-ARR target. |
| 2026-09-15 | Milestone 2 observation | Rechecked both services after the overnight observation: direct and friendly paths, all three DNS authorities, NPM syntax, Beszel identity/password state, all seven agents and both Git refs. | Passed without regression; Milestone 3 could begin. |
| 2026-09-15 | Grafana native OIDC | With explicit Stream-M approval, captured validated Authentik and Grafana checkpoints, narrowed the pre-existing Grafana application binding from the two-member `authentik Admins` group to direct owner `jason`, and enabled Generic OAuth against existing provider 10. Protected environment and INI credentials matched; all temporary transfer/setup files were removed. The first real callback exchanged tokens successfully but strict role evaluation rejected a constant expression; replacing it with the supported `contains(groups[*], 'authentik Admins') && 'Admin' || 'Viewer'` expression resolved the failure. | Passed. Private iPhone Safari authentication reached the provisioned HomeLab overview as organization Admin; sign-out returned to both login choices. The original local server admin and direct login remain active, `jason`/`akadmin` policy evaluates allow/deny, SQLite integrity is `ok`, NPM syntax passes, Grafana health/database are `ok`, and Homepage/Beszel regressions pass. |
| 2026-09-15 | Milestone 3 ARR package recovery checkpoint | Read-only discovery confirmed Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd are one Dockge Compose project on `192.168.20.40`; all five direct UIs return 200 and existing API-key integrations remain out of scope. With explicit Stream-M approval, captured root-only Authentik PostgreSQL/Compose, NPM SQLite, OPNsense XML, both Pi-hole, Homepage services, ARR Compose and per-application configuration checkpoints. Used SQLite online backups for the four ARR databases and NPM; copied SABnzbd configuration. | Passed. All five SQLite integrity checks returned `ok`, Authentik's dump enumerated with `pg_restore`, OPNsense XML parsed, artifacts are mode `0600` in protected directories, NPM syntax passes, identity containers remain healthy, all five ARR containers remain up and every direct UI still returns 200. No routing, DNS, identity or application behavior changed. |
| 2026-09-15 | Milestone 3 ARR shared network gate | With explicit Stream-M approval, added OPNsense port alias `ARR_UI_PORTS` containing only TCP 8989, 7878, 8686, 9696 and 8080, plus one logged pass rule from NPM `192.168.50.23` to ARR host `192.168.20.40` using that alias. | Passed. The persistent model contains exactly one alias and rule; the loaded ruleset expands to exactly the five approved ports. Requests originating inside NPM return 200 from all five services, while the same host's unapproved Dozzle port 8888 still times out. All five direct URLs remain HTTP 200. |
| 2026-09-15 | Milestone 3 ARR identity and reverse-proxy gate | With explicit Stream-M approval, atomically created five dedicated Authentik forward-single providers/applications for Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd, each with exactly one direct enabled `jason` binding, and attached all five providers to the embedded outpost. Created five matching NPM hosts (IDs 10–14) to the existing direct ports with wildcard certificate 8, forced TLS, HTTP/2, WebSockets, exploit blocking and the established minimal forward-auth configuration. Added only `sabnzbd.elliottrook.com` to SABnzbd's host allowlist and restarted that container. | Passed before DNS publication. Authentik read-back confirms the five external/internal mappings, owner-only bindings and outpost membership. NPM SQLite integrity and `nginx -t` pass; certificate-valid pinned requests to all five names return same-host Authentik 302 redirects. All five containers are running and direct URLs remain HTTP 200; SABnzbd's new hostname occurs exactly once. Existing API-key paths and application authentication settings were not changed. |
| 2026-09-15 | Milestone 3 ARR split-DNS gate | With explicit Stream-M approval, added all five friendly ARR names to OPNsense Unbound and both Pi-hole `dns.hosts` arrays, each resolving privately to NPM `192.168.50.23`; restarted each redundant Pi-hole separately and reloaded/restarted Unbound after its configuration check passed. | Passed. OPNsense and both Pi-holes independently return `192.168.50.23` for every name; both Pi-holes are healthy. Normal certificate-valid HTTPS requests to all five names return their same-host Authentik 302 start routes. Homepage, Beszel and Grafana retained their expected 302/200/302 responses. |
| 2026-09-15 | Milestone 3 ARR forward-auth correction | Jason's first private-iPhone Sonarr test reached Authentik but showed `Redirect URI Error`. Live request evidence proved the generated callback was correct while all five directly-created providers lacked the callback, standard scope and grant-type fields normally populated by Authentik's serializer. With separate explicit approvals, populated two hostname-specific strict callbacks, copied the established five default proxy/OIDC scope mappings and the standard authorization-code/client-credentials/password grant set to all five providers. A diagnostic comparison inadvertently emitted Homepage's and Sonarr's provider cookie secrets, so all six affected provider cookie secrets were immediately rotated with approval. | Corrected. Read-back shows every provider has exactly two strict callbacks, five mappings, three expected grants and a unique 32-character cookie secret. Complete cookie-preserving unauthenticated requests to all five friendly names now reach the Authentik login flow with HTTP 200 rather than an error. No user password, application API key or OAuth client secret was exposed; existing direct paths remain unchanged. |
| 2026-09-15 | Milestone 3 ARR interactive authentication gate | Jason used Private Safari on iPhone to complete a real Authentik login to Sonarr, then opened Radarr, Lidarr, Prowlarr and SABnzbd successfully through the same SSO session. The Sonarr outpost sign-out endpoint ended the session and revisiting Sonarr required authentication again. | Passed for the coordinated five-service package. Uncached policy evaluation allows `jason` and denies `akadmin` for every application. NPM syntax and database integrity pass; all containers and direct paths remain healthy. Existing application authentication modes are unchanged, and direct authenticated API probes return 200 for Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd. |
| 2026-09-15 | Milestone 3 ARR Homepage cutover | With explicit Stream-M approval, changed only the five ARR tile `href` values to their private HTTPS names. Retained every widget `url` on its direct `192.168.20.40` endpoint and retained all file-backed API-key references. | Coordinated ARR package complete. Homepage rendered all five HTTPS links, remained healthy and returned 200; each direct widget URL remains present exactly once, and all five direct service URLs return 200. |
| 2026-09-15 | Milestone 3 Portainer discovery and recovery checkpoint | Selected Portainer as the next individual package. Read-only audit found CE `2.39.5`, internal authentication, healthy direct HTTP/HTTPS paths, no NPM/Auth/DNS objects and no NPM-to-backend firewall path. With explicit Stream-M approval, briefly stopped Portainer for a consistent archive of its Bolt-backed data volume and saved container metadata; also captured fresh protected Authentik, NPM, OPNsense, both Pi-hole and Homepage checkpoints. | Passed. Portainer restarted at the same version and both direct paths return 200; its archive lists cleanly and has a recorded SHA-256 hash. Authentik remains healthy, NPM backup integrity is `ok` with 14 active hosts, NPM syntax passes, OPNsense XML parses and all artifacts are mode `0600` in protected directories. No live behavior changed. |
| 2026-09-15 | Milestone 3 Portainer network gate | With explicit Stream-M approval, added one logged OPNsense pass rule from NPM `192.168.50.23` to Portainer `192.168.20.20:9000`. | Passed. Persistent and loaded state contain exactly that source, destination and TCP port. Portainer returns 200 from inside NPM on 9000 while direct HTTPS port 9443 still times out from NPM; both trusted-client direct paths remain HTTP 200. |
| 2026-09-15 | Milestone 3 Portainer private HTTPS | With explicit Stream-M approval, created NPM host 15 for `portainer.elliottrook.com` to `192.168.20.20:9000` using wildcard certificate 8, forced TLS, HTTP/2, WebSockets and exploit blocking; no forward-auth configuration was added because Portainer uses native OAuth. | Passed before DNS publication. NPM SQLite integrity and syntax pass; pinned certificate-valid root, API status and friendly-Origin requests return 200 at Portainer `2.39.5`. Direct HTTP/HTTPS and Homepage remain 200. |
| 2026-09-15 | Milestone 3 Portainer native OAuth candidate | With explicit Stream-M approval, created confidential Authentik provider 22/application `portainer`, one strict root callback, the default OpenID/profile/email mappings plus dedicated `portainer-admin` mapping, and exactly one direct `jason` binding. Configured Portainer for authorization-code OAuth, SSO and the `portainer_username` claim with automatic user creation disabled. A first cross-host credential handoff did not deliver the file and changed no Portainer setting; the same provider credentials were then transferred through protected mode-0600 temporary files and all copies were removed. | Passed before DNS publication. A complete cookie-preserving authorization request reaches Authentik's login flow. Authentik allows `jason` and denies `akadmin`; Portainer retains exactly initial admin ID 1/role 1, its existing Homepage API token returns 200, direct access remains healthy and no trusted-origin change was required. No credential was printed or committed. |
| 2026-09-15 | Milestone 3 Portainer split DNS | With explicit Stream-M approval, added `portainer.elliottrook.com -> 192.168.50.23` to OPNsense Unbound and both Pi-hole `dns.hosts` arrays, reloading Unbound after its configuration check and restarting the redundant Pi-holes one at a time. | Passed. All three authorities independently return NPM's address; both Pi-holes are healthy. Normal certificate-valid Portainer root and friendly-Origin API requests return 200, while Homepage, Beszel, Grafana and Sonarr retain their expected responses. |
| 2026-09-15 | Milestone 3 Portainer interactive authentication gate | Jason used Private Safari on iPhone to complete Authentik OAuth and reached the existing Portainer `admin` account and local environment. Logging out ended the Portainer session; revisiting the friendly URL required authentication again. Jason separately confirmed that the direct `https://192.168.20.20:9443` local-admin break-glass login still works. | Passed. The owner login, same-host return, session termination and local recovery path are proven. The pre-cutover Authentik policy evaluation still allows only `jason` and denies `akadmin`; automatic user creation remains disabled. |
| 2026-09-15 | Milestone 3 Portainer Homepage cutover | With explicit Stream-M approval, changed only Portainer's Homepage tile `href` from the direct recovery URL to `https://portainer.elliottrook.com`. Retained the widget URL at direct `https://192.168.20.20:9443`, environment ID 3 and its file-backed API key. | Portainer package complete. Homepage and both Portainer direct paths return 200, the existing API token returns 200 from the widget endpoint, the friendly route returns 200, all three private DNS authorities return NPM's address, and NPM database integrity and syntax pass. Existing Homepage, Beszel and Sonarr paths retain their expected responses. |
| 2026-09-15 | Milestone 3 Pi-hole pair discovery and recovery checkpoint | Selected the redundant Pi-hole web interfaces as one coordinated package. Read-only discovery found primary `2026.05.0` healthy on `192.168.20.20:8082` and secondary `2026.07.2` running on `192.168.20.40:20720`; both DNS services answer correctly, neither proposed hostname exists, and NPM times out reaching both web ports. With explicit Stream-M approval, captured fresh protected Authentik PostgreSQL/Compose, NPM SQLite, OPNsense XML, primary and secondary Pi-hole configuration, TrueNAS application configuration and Homepage services checkpoints. | Passed without changing live behavior. The Authentik dump lists 1,818 archive entries; NPM SQLite integrity is `ok`; OPNsense XML parses; all checkpoint files are mode `0600` in mode-`0700` directories and have recorded SHA-256 hashes. Both Pi-holes remain healthy/running, their direct web responses are unchanged and each DNS server still returns the expected private Portainer record. Next gate requires exactly two web-only firewall rules; TCP/UDP 53 remains untouched. |
| 2026-09-15 | Milestone 3 Pi-hole pair network gate | With explicit Stream-M approval, added two logged OPNsense pass rules: NPM `192.168.50.23` to primary `192.168.20.20:8082` TCP and to secondary `192.168.20.40:20720` TCP. | Passed. Persistent model and loaded `pf` state contain exactly those source/destination/port tuples. Requests from inside NPM now receive the primary's normal 302 login redirect and the secondary's normal 200 response. NPM remains blocked from the unapproved Portainer HTTPS control port; both Pi-hole DNS servers and direct web paths remain healthy. TCP/UDP 53 configuration was not changed. |
| 2026-09-15 | Milestone 3 Pi-hole pair friendly-host compatibility | Reverse-proxy preflight returned 403 from both Pi-hole v6 webservers when presented with their future friendly Host headers. After checking the current official Pi-hole configuration reference and receiving explicit approval, set primary `webserver.domain` to `dns1.elliottrook.com` and secondary to `dns2.elliottrook.com` using the preferred `pihole-FTL --config` interface, one server at a time. | Passed. Both applications report the exact configured value, remain running/healthy and continue answering DNS. Direct-IP recovery remains available; each friendly Host request from NPM now receives the expected 308 redirect to `/admin/` instead of 403. No DNS, filter-list or application-login setting changed. |
| 2026-09-15 | Milestone 3 credential-exposure correction | While inspecting Sonarr provider 17 as the known-good forward-auth template, a diagnostic printed its OAuth client secret. Work stopped before Pi-hole objects were created. With separate explicit approval, rotated only that provider secret and waited for the embedded outpost to synchronize. | Corrected. Sonarr's cookie-preserving unauthenticated route reaches the Authentik login flow, NPM syntax passes and every ARR direct UI returns 200. No Sonarr data, API key, application setting, download workflow or other ARR provider changed. |
| 2026-09-15 | Milestone 3 Pi-hole pair identity and reverse-proxy gate | With explicit Stream-M approval, atomically created forward-single providers 23-24 and applications `pihole-primary`/`pihole-secondary`, each with exactly one direct enabled `jason` binding, two strict hostname-specific callbacks, five standard mappings, three expected grants and embedded-outpost attachment. Created NPM hosts 16-17 for `dns1` and `dns2` to the existing HTTP ports with wildcard certificate 8, forced TLS, HTTP/2, WebSockets, exploit blocking and the established minimal Authentik forward-auth configuration. The first pinned requests arrived before the outpost refresh and returned 500 from an upstream 404; the outpost then reported both applications loaded and no configuration correction was required. | Passed before DNS publication. Both pinned certificate-valid names now return same-host Authentik 302 start routes and complete cookie-preserving requests reach the Authentik login flow with 200. Authentik read-back confirms every field and owner binding; NPM SQLite integrity and syntax pass. Both Pi-hole direct interfaces and DNS services are healthy, and Sonarr retains its expected 302. |
| 2026-09-15 | Milestone 3 Pi-hole pair split DNS | With explicit Stream-M approval, added `dns1.elliottrook.com` and `dns2.elliottrook.com`, both pointing to NPM `192.168.50.23`, to OPNsense Unbound and both Pi-hole `dns.hosts` lists. Validated and reloaded Unbound, then restarted the redundant Pi-holes one at a time, proving the other resolver remained available before continuing. | Passed. OPNsense and both Pi-holes independently return the intended address for both names, as does the normal client resolver. Both Pi-holes are healthy and continue serving DNS; direct web recovery is unchanged. Normal certificate-valid HTTPS requests return the correct same-host Authentik 302 routes, while NPM SQLite integrity and syntax pass. |
| 2026-09-15 | Milestone 3 Pi-hole pair interactive authentication gate | Jason used Private Safari on iPhone to authenticate through `dns1`, then completed the deliberately retained primary Pi-hole password login and reached its dashboard. The secondary dashboard also worked through the same Authentik SSO session. Opening the `dns1` outpost sign-out route and revisiting the site required Authentik again. | Passed. Real sign-in, SSO, application login and Authentik session termination are proven for the coordinated pair. Fresh uncached policy evaluation allows `jason` and denies `akadmin` for both applications. Direct web recovery and both DNS services remain available. |
| 2026-09-15 | Milestone 3 Pi-hole pair Homepage cutover | With explicit Stream-M approval, changed only the primary and secondary Pi-hole tile `href` values to `https://dns1.elliottrook.com` and `https://dns2.elliottrook.com`. Retained the primary widget URL at direct `http://192.168.20.20:8082`, version 6 and its file-backed credential. | Coordinated Pi-hole package complete. Homepage is healthy and the direct authenticated widget API returns 200. Both friendly routes retain their Authentik 302 gates; all three DNS authorities return NPM's address; NPM database integrity and syntax pass. Homepage, Beszel, Sonarr and Portainer retain their expected responses. |
| 2026-09-15 | Remaining-work scale redesign | Jason directed that the large remaining rollout be chunked by shared implementation layer rather than completed one service at a time. Reconciled the project scope with the onboarding plan: Frigate's browser UI is in Milestone 3, Plex is assessment-only/no-change by default, Milestone 5 is explicitly defined, and remaining applications/infrastructure are divided into risk-based cohorts. | Design only; no live state changed. Each cohort now batches discovery/checkpoints, network/proxy staging, Authentik objects and DNS publication while preserving per-application native-OIDC secret handling, recovery, client tests and independent promotion. Stream M per-change approval and stop-on-surprise rules remain unchanged. |

## Close-out

Not graduated. Stream A is active as of Jason's 2026-09-23 approval.
Previously graduated packages remain in place; six further routes are staged
with automated gates passed and human acceptance pending. Forgejo's owner
binding is fixed and an isolated Authentik database restore passed. Newtarr's
persistence risk, Frigate/Immich checkpoint access, remaining media/native
identity work, infrastructure workflows, stale-session confirmation and final
integration/rebuild gates remain open. Resume from the dated audit and exact
object inventory near the start of this document; do not recreate staged
objects or promote unaccepted Homepage links. Remote Git synchronization
requires immediate approval and is not implied by Stream A.
