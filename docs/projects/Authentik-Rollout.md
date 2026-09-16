# Authentik Service Rollout Project

> Status: Active — Milestone 2 complete; Milestone 3 Grafana package complete
> 2026-09-15, next package not started.
> Live baseline re-audited 2026-09-13. Redesigned 2026-09-10
> under [HomeLab Project Creation Standard](../Project-Creation-Standard.md).
> Stream: **M — Monitored**. Handed off 2026-09-10 to a fresh local session
> for Jason to drive via remote approval — see "Starting the handoff
> session" below before doing anything else.
>
> Owner: Jason
>
> Proposed: 2026-08-22 · Redesigned: 2026-09-10

## Starting the handoff session

If you are a new session picking this project up: read this entire
document plus `docs/09-Service-Authorization-Onboarding.md` before touching
anything, then start at Milestone 1 (not Milestone 2 — it was never
re-verified after the redesign). This is a **Stream M** project: present
each state-changing step (target, exact change, expected effect, validation,
rollback) and wait for Jason's approval before running it. He is expected to
be approving remotely from his phone, not sitting at this Mac, so:

- Batch only what the Standard allows — commands that implement one clearly
  bounded, reversible change and share the same risk — into a single
  approval ask. Don't ask once per trivial sub-step, and don't bundle
  unrelated changes into one ask either.
- Assume delay between an ask and a response. Don't leave anything
  mid-change (e.g. old config removed, new config not yet validated) while
  waiting — each approved step should land in a complete, working state
  before the next ask goes out.
- If nothing is approved for a while, that's normal for this mode; don't
  fall back to acting without approval, and don't repeat the sandbox
  incident's mistake of "fixing" the wait by finding a workaround that
  expands scope.
- Read-only discovery and planning need no approval at all (already
  pre-agreed per the Standard) — only state-changing steps do.

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
ever down. This is a service-by-service rollout, not a bulk conversion.

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
- **Homepage, Beszel — not started, re-confirmed live 2026-09-13.** Homepage
  is healthy at `http://192.168.20.20:3000`; Beszel `0.18.7` is healthy at
  `http://192.168.20.20:8090`. NPM has no proxy host for either intended
  hostname, Authentik has no Homepage/Beszel application or provider, and
  `home.elliottrook.com` / `metrics.elliottrook.com` return no A record from
  OPNsense or either Pi-hole. The direct fallbacks remain intact.
- Full live dashboard inventory pulled 2026-09-10 (`/opt/homepage/config/services.yaml`)
  — ~35 apps total, most never previously scoped in this project. See Scope
  below and `docs/09-Service-Authorization-Onboarding.md`'s service plan
  table for the per-service detail.

## Scope and exclusions

**In scope for this redesign pass:** Milestone 2 — Homepage and Beszel only.
Milestones 3 (operations/application wave — Portainer, Pi-hole, Immich,
Seerr, the *arr stack, Grafana, Code Server, Dockge, Dozzle, Homarr,
Newtarr, File Browser, NetBox, Calibre/Audiobookshelf, Jellyfin) and 4
(infrastructure interfaces — Proxmox, TrueNAS, Synology, UniFi, Home
Assistant, OPNsense) remain explicitly out of scope until Milestone 2
graduates and is observed stable. This project's own principle, unchanged
from before the redesign: one service at a time, observe before the next
wave.

**Milestone 3 packaging decision:** treat the operational *arr stack as one
coordinated work package, not five sequential service rollouts. Its fixed
membership is Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd, matching
`docs/ARR-Stack-Operational-Reference.md`. Design, approve, back up, implement,
validate and roll back that package behind one shared gate. Each browser UI may
still require its own hostname, NPM host and Authentik application, but those
are components of one atomic work package. Preserve every existing API-key
path among Prowlarr, the three ARR applications, SABnzbd, Homepage and the
automation tools; Authentik applies only to human browser access. The general
one-service-at-a-time rule continues to apply to all other Milestone 3 targets.

**Never proxy through Authentik:** SSH, DNS, SMB, NFS, iSCSI, RTSP, ONVIF,
backup transports, the Ollama-compatible API, the Tailscale control path.
Confirmed additions from the full dashboard inventory: the AP Switch's raw
HTTP management page, Aster llama.cpp's inference API, GitHub (external,
own auth). Do not make firewall recovery depend on Authentik or the reverse
proxy.

**Excluded from autonomous/unattended execution specifically** (see
Persistence plan below): any step requiring raw SSH/TCP verification, any
step requiring a real browser-based login test, any OPNsense change beyond
what's explicitly pre-approved per action.

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

## Privacy and security design

- Homepage forward auth gates the dashboard's browser UI only; its
  own widget calls to backend services (Portainer, Proxmox, TrueNAS, Sonarr,
  etc.) run server-side from the Homepage container itself and are
  unaffected by adding a login gate in front of the dashboard page.
- Beszel: if forward auth is used instead of native OIDC, its monitoring
  agents (on every other host) must keep using their existing private
  direct connection to the hub — never route agent-to-hub traffic through
  Authentik.
- Least privilege: bind both services to an explicit Authentik group
  (`homelab-admins` or a narrower family group, per whatever Milestone 1's
  actual current group set is — verify live rather than assume, see
  Milestone 2 below), not open to every Authentik identity by default.
- No credential, client secret, or API key from this rollout is committed
  to Git or printed in this document; only their storage location.

## Pre-start risk assessment

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
- **Unresolved decision:** whether Beszel's installed version supports
  native OIDC — not yet confirmed live, first action of its own step below.

## Persistence plan

Per the new Standard's persistence requirements:

- This document and its Evidence log are the durable state. Before any
  state-changing step, the current milestone, next action and rollback
  location are recorded here — not held only in conversational memory.
- No long-running unattended job is used for this project's remaining work
  at this time. Given the confirmed SSH/sandbox constraint above, Milestone
  2's steps run in an attended (Stream M) session: read-only discovery and
  API-based configuration can proceed without per-step approval per the
  Standard's "Standard authorization common to all projects," but each
  state-changing step is presented with target/change/effect/validation/
  rollback and approved immediately before it runs.
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

Work one bounded package at a time. The ARR stack is the single coordinated
five-application package defined in the scope decision above; every other
target remains an individual package.

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

**Next package:** not started. Select and design it only after Grafana's short
stability observation; the ARR stack remains one coordinated package.

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

Milestone 2 graduates when Homepage and Beszel are both live on friendly
HTTPS names, validated end-to-end by a real login, direct fallback proven,
and the onboarding completion record updated for both. The whole project
graduates only after Milestones 3, 4 and 5 (unchanged, not started) also
pass their own gates — this redesign closes out Milestone 0 and resets
Milestone 2 to a safely resumable state, it does not graduate the project.

## Evidence log

| Date | Item | Evidence | Result |
|---|---|---|---|
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

## Close-out

Not graduated. Deferred/open: closing the two stalled sessions directly
(needs Jason, not reachable from this session); Milestones 1-2 live
re-verification and execution; Milestones 3-5 unchanged and still future
work.
