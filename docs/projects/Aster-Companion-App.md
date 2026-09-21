# Aster Companion App

> Status: Proposed — Stream A requested by Jason; pre-start risk assessment
> below requires his explicit acceptance before Milestone 2 (first
> state-changing work) begins, per the Standard's Stream A gate.
>
> Project owner: Jason
>
> Proposed: 2026-09-21
>
> Authorization stream: **Stream A — Autonomous**, assigned by Jason at
> proposal time. Per `docs/Project-Creation-Standard.md`, the pre-start risk
> assessment below is the authorization envelope; work starts only after
> Jason accepts it. Milestone 1 (discovery/design, all read-only or
> documentation-only) is pre-agreed under the Standard's common authorization
> and is already underway in this document.

## Purpose and desired outcome

A native macOS client ("Aster Companion") that gives Jason a first-class way
to talk to Aster — locally on the lab network and remotely — instead of the
existing bare-bones browser page. Concretely:

- Sign in once with Authentik, using a passkey only (no password prompt).
- Talk to Aster by voice: speech-to-text for Jason, text-to-speech for
  Aster's replies, with a visual indicator (an "orb"/EQ-style graphic) that
  shows distinct idle/listening/thinking/speaking/acting states.
- Choose which **Aster Agent** (a named persona — e.g. "Sysadmin Aster,"
  "Media Automation Aster") a conversation talks to, so a chat only carries
  the system prompt, knowledge scope and tool set relevant to that persona
  instead of every capability Aster has, all the time.
- Within a conversation, choose which of that persona's tools are actually
  enabled for that chat, rather than always exposing everything a persona
  could theoretically use.
- Work the same way whether Jason is on the lab LAN or away from it, without
  a different login flow or a different app mode for each case.

This is explicitly a client and identity/interface project, not a rebuild of
Aster's own model, inference backend or knowledge pipeline. Aster's existing
`aster-llama` inference, knowledge snapshot and sanitized source reports
(`docs/reference/Aster-Operations.md`) remain exactly as they are; this
project adds a new front door and, per an explicit design decision recorded
below, a bounded first step toward Aster taking gated actions rather than
only ever answering questions.

## Current state and evidence

- **Aster today** runs as `aster-agent.service` on LXC 104 (`192.168.70.10:9120`,
  Lab VLAN 70), calling `aster-llama.service` on LXC 110
  (`192.168.70.12:11435/v1`, Qwen3.8 27B on an Intel Arc Pro B60, one
  8,192-token slot, single-user). Source is git-tracked in this repository at
  `services/aster-agent/aster_agent.py` with an existing test suite
  (`services/aster-agent/test_aster_agent.py`) — this project can extend it
  with normal code review and tests, unlike some other lab services whose
  deployed source lives only on the guest.
- **Auth today** is a single static bearer key (`ASTER_API_KEY`), checked by
  `require_api_key()` in `aster_agent.py`. The existing browser page
  (`GET /`) stores that key in the browser's local storage and calls
  `POST /v1/chat/completions` directly. There is no Authentik involvement and
  no per-user identity — anyone with the key has full access.
- **Tool selection today** is keyword-based and pre-execution, not a model
  driven tool-call loop: `select_tools(messages)` inspects the incoming
  conversation text and `preload_read_only_context()` executes whichever of
  Aster's eight allowlisted read-only functions match, before the single
  call to `aster-llama`. The model itself never requests a follow-up tool
  call in production — this is a deliberate one-pass design
  (`docs/reference/Aster-Operations.md`, "Functions and knowledge").
- **The one existing mutating capability** is the ARR queue-record repair
  (`docs/projects/completed projects/Aster-Arr-Stack-Manager.md`,
  `docs/projects/Aster-ARR-First-Repair-Decision.md`). It is fully
  implemented and tested (`services/aster-arr-broker/`) but the broker is
  stopped and boot-disabled by default, binds to loopback only, requires an
  explicit temporary OPNsense rule and `ASTER_ARR_EXECUTION_ENABLED=true` to
  do anything, issues one opaque single-use candidate per eligible record,
  and needs a fresh operator-only approval (two-minute expiry) for every
  live attempt. There is no standing execution authority anywhere in the
  current design — this is the shape any future gated action in this project
  must follow.
- **Authentik** is `2026.8.0` (last confirmed live 2026-09-13,
  `docs/projects/Authentik-Rollout.md`) and already runs native OIDC for
  Forgejo, Beszel, Grafana and the five ARR web UIs, each as its own
  dedicated OAuth2/OIDC provider + application with a strict callback, PKCE
  where applicable, and exactly one direct `jason` binding. `jason` already
  has a working WebAuthn passkey ("Apple Passwords," live since 2026-09-10).
  Every existing flow is **password + passkey** (two-factor). A true
  passwordless (passkey-only, no password stage) flow does not exist
  anywhere in this lab yet and needs live verification in Milestone 1 that
  the installed Authentik version actually supports an
  identification-stage-plus-WebAuthn flow with no password stage.
  Every existing native-OIDC client so far has been a **browser-based web
  app** behind NPM; there is no precedent yet for a genuine native
  (non-browser) OIDC client in this lab, so the exact callback mechanism
  (custom URL scheme vs. loopback redirect via `ASWebAuthenticationSession`)
  needs a Milestone 1 spike, not an assumption.
- **Network reachability:** Aster's LXC 104 sits on Lab VLAN 70. Tailscale's
  subnet router (`homelab-gateway`, Docker LXC 100) currently advertises only
  Trusted (`192.168.1.0/24`), Servers (`192.168.20.0/24`) and Management
  (`192.168.50.0/24`) routes to the administrator identity
  (`docs/Current-Network-Baseline.md`) — **not** Lab VLAN 70. So today,
  nothing on Lab VLAN 70 (Aster, `aster-llama`, MuckScraper) is reachable
  over Tailscale at all; local reachability from Jason's three named devices
  is via a separate, narrow OPNsense rule pattern already used for the news
  aggregator (`MGMT_ADMIN_HOSTS → 192.168.70.13:8080/tcp`,
  `docs/projects/Combined-Morning-Digest.md`) — worth confirming live whether
  an equivalent rule already exists for `192.168.70.10:9120`.
- **Speech:** Piper TTS (`en_US-lessac-medium`, `length_scale 1.15`) is
  already vetted and in production for the news aggregator's audio digest
  (`docs/projects/completed projects/News-Aggregator-Audio-Digest.md`), which
  explicitly named itself "a trial for a planned Home Assistant project" —
  this project is a second real consumer of that same vetted voice. No local
  speech-to-text engine is deployed anywhere in this lab yet; the proposed
  (not yet built) Home Assistant voice assistant
  (`docs/projects/Home-Assistant-Voice-Assistant.md`) and subtitle project
  (`docs/projects/Subtitle-Generation-Translation.md`) both anticipate
  Whisper-family STT but neither has deployed it.
- **Existing Mac-native-app precedent:** the FreeCAD MCP connector
  (`docs/projects/FreeCAD-MCP-Connector.md`) is the only prior "runs
  natively on this Mac" project, but it is a localhost bridge process, not a
  GUI app with its own identity/UI — limited architectural overlap.

## Scope

- A native macOS app (SwiftUI), the v1 client, explicitly designed to extend
  to other Apple platforms (iOS/iPadOS) later without a rewrite — but iOS is
  not built in this project.
- Authentik login using a new, dedicated passwordless (passkey-only) OIDC
  flow and application, via the system browser (`ASWebAuthenticationSession`)
  and PKCE, with the resulting token stored in the macOS Keychain.
- A reverse-proxied, Authentik-fronted HTTPS endpoint for Aster's chat API
  (new NPM host + narrow OPNsense rule), used identically whether Jason is on
  the LAN or remote over Tailscale — one code path, matching how
  Homepage/Beszel/Grafana already work "locally and remotely" via split-DNS.
- Extending `aster_agent.py` to accept Authentik-issued access tokens as a
  second, additive credential type alongside the existing static bearer key
  (no regression to the existing browser page).
- An **Aster Agents** concept: named personas, each a bundle of {system
  prompt/framing, knowledge scope, allowed tool set}, served by the same
  backend/model rather than separate deployments (the shared B60/one-slot
  inference backend cannot support multiple concurrent model deployments).
  Two personas ship in this project: **Sysadmin Aster** (today's existing
  capabilities/knowledge, unchanged) and **Media Automation Aster** (ARR
  stack-focused: the existing sanitized ARR report and, per the decision
  below, the existing ARR-repair action).
- A per-chat tool selector: within a conversation, choose which of the
  active persona's available tools are actually eligible for that chat.
- **A recorded, explicit architecture-philosophy shift**, per Jason's
  direction: Aster moves from "strictly read-only, one-pass" toward
  incrementally more autonomous, more capable, on a deliberately bounded
  path. This project's own concrete step on that path is: generalize the
  existing ARR-repair broker's shape (dry-run, opaque single-use candidate,
  operator-only time-boxed approval, audit log, no standing authority) into
  a reusable "gated action" contract, and surface the **existing** ARR-repair
  action through it in the app. This project does **not** invent new
  mutating capabilities beyond ARR-repair — see Exclusions.
- A voice pipeline: speech-to-text (Jason) and text-to-speech (Aster),
  centralized as a shared service on a lab host per Jason's decision, rather
  than on-device on the Mac — reusable later by other future clients.
- A visual state indicator (orb/EQ-style graphic) with distinct idle,
  listening, thinking, speaking and acting states — "acting" must be visually
  unmistakable from "thinking," since one of them may mutate state and the
  other never does.

## Out of scope (exclusions)

- **Any new mutating capability beyond the existing ARR-repair action.**
  Jason's direction to move Aster toward "more autonomous, more features"
  is recorded above as an accepted long-term philosophy, but this project
  does not itself pre-authorize building new action brokers (e.g. "restart
  a service," "trigger a Sonarr search," "modify a file"). Each new gated
  action is a materially different capability and, per the Standard's
  non-waivable stop conditions, needs its own explicit risk decision when it
  is actually proposed. This project builds the reusable *framework* and
  wires up the one action that already exists and is already fully
  risk-assessed.
- **Web access for Aster (research/browsing).** Named by Jason as the "next
  step" after this project. Explicitly and deliberately **not** in this
  project's scope: outbound internet access from Aster's context is a new
  egress path, a new prompt-injection attack surface (untrusted fetched
  content entering the model's context), and a materially different
  objective from this project's client/identity focus. It needs its own
  full project document, pre-start risk assessment and stream decision.
  Recorded here only so the intent isn't lost.
- Any change to `aster-llama`'s model, hardware, or inference configuration.
- Any change to the existing Forgejo/NetBox/Home-Assistant sanitized source
  reports' content or authority boundary.
- Any change to the existing browser page's current bearer-key access — it
  keeps working unmodified; Authentik is additive, not a replacement, in
  this project.
- Building or deploying the proposed Home Assistant voice assistant project
  — that project (if separately authorized) is HA's own Assist pipeline for
  household device control and is unrelated to this app talking to Aster.
- Windows/Linux/web clients, and iOS/iPadOS builds (architected for, not
  built).
- Widening Tailscale's advertised routes to include Lab VLAN 70 (rejected in
  favor of the NPM+Authentik proxy — see Architecture).

## Authority model

- **Aster (`aster_agent.py`, LXC 104)** remains the sole authority for which
  tools/functions exist, what a persona's system prompt and knowledge scope
  is, and whether a gated action's preconditions are met. This project adds
  new *inputs* (persona selector, enabled-tools list, Authentik token) to
  that existing authority; it does not move any decision-making into the
  client app. The client cannot invoke a function or action the backend
  doesn't already expose for the active persona.
- **Authentik** is the sole authority for who Jason is and whether this
  app's passkey-only flow accepts the credential presented. Aster validates
  Authentik-issued tokens against Authentik's own signing keys; it does not
  maintain its own user database.
- **The ARR broker (`services/aster-arr-broker/`)** remains the sole
  authority for whether a gated action's preconditions hold and whether an
  approval is valid — this project's "gated action" framework is a thin,
  generalized client/contract layer over that existing authority, not a
  replacement for it.
- **This project document** owns the app/identity/voice design, its own risk
  acceptance and milestone evidence. `docs/reference/Aster-Operations.md`
  remains authoritative for Aster's own operational facts and is updated,
  not duplicated, as this project changes Aster's deployed behavior.

## Architecture and data flows (proposed)

```
[Aster Companion (macOS, SwiftUI)]
   |  1. Passkey-only login (system browser, PKCE)
   v
[Authentik 2026.8.0 — new dedicated OIDC provider/application
 "aster-companion", new passwordless flow (identification + WebAuthn only)]
   |  access token (JWT), stored in macOS Keychain
   v
[NPM, new host e.g. aster.elliottrook.com -> 192.168.70.10:9120]
   |  one new narrow OPNsense rule: NPM (Mgmt VLAN 50, 192.168.50.23)
   |  -> Aster API (Lab VLAN 70, 192.168.70.10:9120) only
   v
[aster_agent.py, LXC 104 — extended to accept Authentik tokens
 alongside the existing static bearer key; persona + enabled-tools
 request fields; existing one-pass function preload unchanged]
   |                                  |
   v                                  v
[aster-llama /v1, LXC 110]   [aster-arr-broker "gated action" path,
                               existing dry-run/approval/execute shape,
                               unchanged, reused not rebuilt]

[Speech, centralized lab service — placement decided in Milestone 1]
   Mac app <--HTTPS, same Authentik-fronted ingress, new /voice path-->
   [STT (e.g. faster-whisper, CPU) + TTS (Piper, en_US-lessac-medium)]
```

Local and remote access use the **same** hostname and the **same** login
flow: split-DNS resolves `aster.elliottrook.com` to NPM's internal address
for LAN clients, and Tailscale's already-advertised Management-VLAN route
carries the same request when Jason is remote — matching exactly how
Homepage, Beszel and Grafana already behave today. No new Tailscale route is
added.

Open architecture questions for Milestone 1 (not assumed here):

- Exact native-app OIDC callback mechanism Authentik/AppAuth support cleanly
  for a real native macOS app (custom URL scheme vs. loopback redirect).
- Live confirmation that Authentik `2026.8.0` (or whatever is live at
  build time) supports an identification-stage + WebAuthn-only flow with
  no password stage, and that Jason's existing "Apple Passwords" passkey
  authenticates against it without re-enrollment. **Resolved 2026-09-21,
  without needing the (still-unrotated) Authentik API token:** read-only
  `docker exec` into LXC 106 confirmed the live version as `2026.8.0` three
  independent ways (image tag `ghcr.io/goauthentik/server:2026.8.0`, the
  `ak` CLI's own boot log, and the deployment's own record) — no drift from
  what's already documented. A read-only Postgres query
  (`authentik_flows_flow`) shows only the 15 stock default flows exist; no
  custom passwordless flow has been created yet. A second read-only query
  of `default-authentication-flow`'s stage bindings confirms today's real
  stage order: identification (10) → password (20) → mfa-validation (30) →
  login (100), matching `CLAUDE.md`'s "password + passkey" description
  exactly. Critically, `authentik_stages_identification_identificationstage`
  has a native `passwordless_flow` foreign-key column in this version —
  Authentik's own built-in mechanism for offering a passkey-only path
  (skipping the password stage entirely) from the identification screen.
  **This is first-class supported, not something to build from scratch on
  generic flow/stage composition.** The concrete M2 shape this implies:
  create one new flow (e.g. `aster-companion-passwordless`) with
  identification → webauthn (mfa-validation) → login stages and no password
  stage, then either point an identification stage's `passwordless_flow` at
  it or bind it directly as the new `aster-companion` provider's own
  authentication flow (providers can override the shared
  `default-authentication-flow`) — either way, nothing shared with
  Forgejo/Grafana/etc.'s login is touched. Still outstanding: whether
  Jason's existing enrolled WebAuthn credential authenticates against a
  freshly created flow without re-enrollment, which needs an actual test
  flow to exist (M2, not M1).
  **Separate finding worth flagging:** the same `docker exec` access that
  answered this also confirms Authentik's Django management CLI (`ak`) is
  reachable via SSH+`pct exec`+`docker exec`, independent of the HTTPS API
  and its token entirely. That means M2's actual object creation (new flow,
  stages, provider, application) could plausibly be done this way instead
  of via `scripts/api-get.sh` and a rotated `AUTHENTIK_TOKEN` — worth
  deciding with Jason before M2, since it changes which credential (if any)
  needs to exist at all. Every read here was `SELECT`/inspection only; no
  row was written, no flow was created, and the boot log incidentally shows
  `"Enabled authentik enterprise"` — not investigated further, flagging
  only because it wasn't mentioned in any prior project doc.
- Placement of the speech service: a new dedicated Lab VLAN 70 LXC versus
  adding to an existing guest. **Live-confirmed 2026-09-21 via
  `pct list`/`qm list`:** VMID 115 (this document's earlier placeholder) is
  already `paperless-ngx` (`docs/projects/Document-OCR-Summarization.md`,
  deployed 2026-09-15, six days before this project was proposed — the
  placeholder was already stale when written). **116 is the next available
  VMID.** Leaning toward a new dedicated LXC to match the lab's
  one-purpose-per-guest convention (104 agent, 108 Forgejo, 110 inference,
  111 NetBox, 113 wiki, 114 news, 115 Paperless-ngx), but placement itself
  is still not decided.
- Whether `faster-whisper` on CPU meets acceptable STT latency without GPU
  access, given the B60 is already single-slot-committed to `aster-llama`.
- Whether the existing MGMT_ADMIN_HOSTS-style narrow rule already reaches
  `192.168.70.10:9120` today. **Live-confirmed 2026-09-21 via OPNsense's own
  `config.xml`:** no rule anywhere references port 9120 or Aster's host as a
  destination. The two existing `MGMT_ADMIN_HOSTS`-sourced rules are (1) a
  broad `MGMT_ADMIN_HOSTS -> opt4 (any)` rule granting Jason's three named
  devices general reach into Management VLAN 50, and (2) the narrow
  `MGMT_ADMIN_HOSTS -> 192.168.70.13:8080/TCP` rule for the news aggregator
  cited as this project's precedent. **Neither reaches Lab VLAN 70's Aster
  host** — M2 needs a genuinely new narrow rule, not a retirement of an
  existing direct-LAN path (there isn't one).

### Milestone 2 technical prep (drafted during Milestone 1 — research only, no code changes)

Read `services/aster-agent/aster_agent.py` to scope the additive
Authentik-token change ahead of time, without making it:

- `require_api_key()` (line 303) is a plain dependency function: if
  `ASTER_API_KEY` isn't configured it 503s; otherwise it does a single exact
  string comparison of the `Authorization` header against
  `f"Bearer {ASTER_API_KEY}"` and 401s on any mismatch. It has no concept of
  multiple credential types today — extending it means trying the existing
  bearer-key comparison first (unchanged behavior, unchanged error), and
  only on mismatch attempting Authentik-token validation, so the existing
  browser page keeps working exactly as-is.
- Current dependencies are `fastapi==0.133.1`, `httpx==0.28.1`,
  `pydantic==2.13.4`, `uvicorn==0.41.0` — no JWT/JWKS library is present.
  M2 will need to add one (e.g. `PyJWT` with its `crypto` extra, or
  `authlib`), which is a new supply-chain dependency for a production
  service and should be pinned and reviewed like any other, not treated as
  incidental.
- Token validation needs to check `iss` (Authentik's issuer URL) and `aud`
  (the new `aster-companion` OIDC client ID) in addition to signature
  validity against Authentik's JWKS endpoint — signature validity alone
  would accept a token minted for a *different* Authentik application,
  which the Validation section's adversarial test list already calls out.
  JWKS keys should be cached with a bounded TTL rather than fetched per
  request.
- `test_aster_agent.py` has no existing test targeting
  `require_api_key`/`Authorization`/`Bearer` by name (the one existing
  `Bearer` reference at line 743 is unrelated ARR-broker client code), so
  M2's regression gate needs new explicit cases: existing bearer key still
  works unchanged; a valid Authentik token for the correct audience is
  accepted; a valid token for a *different* audience is rejected; an
  expired or malformed token is rejected; a missing `Authorization` header
  still 401s exactly as today.

This is planning only — M1 has not authorized any change to
`aster_agent.py`, and none has been made.

## Privacy and security design

- Passkey-only login means no password is ever transmitted or stored for
  this app's flow — strictly narrower than the lab's existing baseline, not
  broader.
- Recovery path if the passkey device is unavailable: Authentik admin
  (`akadmin`) recovery, matching the lab's existing break-glass pattern.
  Explicitly **not** in scope: weakening the new flow with a password
  fallback to "make recovery easier," which would defeat the purpose of the
  passkey-only decision.
- The Authentik token this app receives is scoped to the `aster-companion`
  OIDC application only; it authenticates the app to Aster (via the new NPM
  proxy) and to the new voice service. It is never given standing authority
  over any other Authentik-fronted application.
- The existing ARR-repair broker's security properties (stopped by default,
  loopback-bound, temporary firewall rule, single-use opaque candidate,
  two-minute approval expiry, full audit log, no retry on failure) are
  unchanged. This project's "gated action" UI in the app triggers the same
  approval flow Jason already uses today; it does not add a new bypass or a
  faster path to execution.
- The new NPM→Aster and NPM→voice-service firewall rules are single-port,
  single-source, single-destination — no broader VLAN-70 exposure is
  created, and Tailscale's advertised routes are unchanged (see Architecture
  for why this is preferred over widening Tailscale).
- Speech audio: since STT/TTS is centralized on a lab host (per decision),
  audio and synthesized speech transit the same Authentik-authenticated
  HTTPS path as chat traffic — no separate unauthenticated audio channel.
  Retention: transient only (processed and discarded), matching the Home
  Assistant voice assistant proposal's same principle, unless Jason later
  asks for debug recording, which must be time-bounded and excluded from
  backup/Aster-visible paths if ever enabled.
- No new inbound Internet path. No new public DNS. No Tailscale Funnel or
  broader tailnet grant.

## Pre-start risk assessment

**Objective/scope/stream:** as defined above. Stream A, assigned by Jason.
Per the Standard, this assessment is the authorization envelope for
Milestones 2 onward; Milestone 1 (discovery/design) is already pre-agreed
and partly reflected above.

**Affected systems:** LXC 104 (Aster Agent — code change, new credential
path), Authentik LXC 106 (new provider/application/flow), NPM LXC 107 (new
host), OPNsense (one new narrow inter-VLAN rule, plus split-DNS entries on
OPNsense Unbound and both Pi-holes), a new Lab VLAN 70 guest for the speech
service (placement TBD in Milestone 1), and Jason's Mac (new native app,
Keychain storage, microphone access).

**Current versions/dependencies:** Authentik `2026.8.0` (reconfirm live at
Milestone 1 start, since this document does not itself re-verify it),
`aster-agent`/`aster-llama` versions per `docs/reference/Aster-Operations.md`,
Piper `en_US-lessac-medium` per the audio-digest project.

**Confidentiality/secret-handling risks:** a new OIDC client secret (if the
client is registered confidential rather than public+PKCE — Milestone 1
decides which) and a new dedicated bearer key for the speech service, both
stored the same way existing Aster-adjacent keys are (root-owned,
group-readable env file, excluded from Git, storage location recorded but
never the value). The Keychain-stored user access token is scoped to this
one app.

**Availability/integrity/privacy/recovery risks:**
- Adding Authentik-token validation to `aster_agent.py` is new code on a
  production path; a bug could lock out the *new* login path without
  affecting the *existing* bearer-key path, since the two are additive —
  the existing browser page is the built-in rollback if the new path
  misbehaves.
- The new voice service adds a new guest and a new narrow firewall path;
  bounded blast radius (STT/TTS only, no HA/ARR/knowledge authority).
- Generalizing the ARR-repair broker into a reusable "gated action" contract
  touches code that already has explicit, hard-won safety properties
  (two-minute approval expiry, opaque single-use candidates, no automatic
  retry on failure). This refactor must not weaken any of those properties;
  Milestone 5's own test suite must re-run the existing ARR-repair test
  suite unchanged as a regression gate, not just add new tests for the
  generalized shape.
- **The recorded philosophy shift itself is the largest open risk in this
  document.** Moving Aster from strictly-read-only toward more autonomous
  over time is a deliberate, accepted direction, but it must be revisited
  explicitly, in its own risk assessment, every time a *new* capability
  class (not just a new instance of an existing one) is proposed — this
  project's own scope boundary (ARR-repair only, no new action classes) is
  the concrete control that keeps today's decision bounded.

**Irreversible/destructive operations:** none anticipated in this project's
own scope. The one mutating action it surfaces (ARR-repair) is the same
already-graduated, already-bounded operation described in
`docs/reference/Aster-Operations.md`; this project changes how it is
*presented and approved*, not what it *does*.

**Expected authentication/firewall/DNS/storage/external-service changes:**
one new Authentik application/provider/flow; one new NPM host (plus a second
for the voice service, or the same host under a different path — Milestone 1
decides); one new narrow OPNsense inter-VLAN rule per new NPM target; two
new split-DNS entries (OPNsense Unbound + both Pi-holes), matching the exact
Beszel/Grafana precedent; one new bearer key (voice service); no change to
existing Aster/ARR/MuckScraper credentials.

**Recovery checkpoint/rollback/abort:** protected pre-change backups of
Authentik (PostgreSQL/Compose) and NPM (SQLite) before any Authentik/NPM
object is created, matching the exact pattern used for every prior
Authentik-Rollout milestone. `aster_agent.py` changes are Git-tracked with
normal commit-level rollback plus a pre-deploy backup copy on LXC 104
(matching the `app.py.bak-YYYYMMDD` convention used elsewhere). Rollback for
the whole project is: disable the new NPM host/OPNsense rule, remove the
Authentik application, and revert `aster_agent.py` to the pre-project
commit — the existing browser page and bearer-key path are unaffected
throughout, so Aster's baseline capability is never at risk during rollback.

**Test strategy:** live verification against the real Authentik/NPM/OPNsense
stack (matching this lab's established pattern — no synthetic Authentik
instance exists or is proposed). The ARR-repair regression suite is real,
existing, and reused, not fabricated. Speech tests use both live voice input
and a synthetic/disposable audio fixture for adversarial cases (silence,
static, no-match utterances).

**Likely service interruption:** none expected to the existing browser page
or any existing `aster-llama` consumer. A capacity risk exists once the
voice service and multi-persona chat add load; Milestone 6 explicitly
re-measures `aster-llama` latency for Aster/MuckScraper alongside this
project's traffic, following the same "measure, don't assume" approach the
Home Assistant voice assistant proposal already calls for.

**Backup/Doctor/monitoring/NetBox/wiki impacts:** see the integration
checklist below.

**Unresolved decisions requiring Jason's acceptance before Milestone 2
begins:**

1. **This document's scope boundary on "mutating actions"** — generalize and
   surface the existing ARR-repair action only; no new action classes. If
   Jason meant something broader by his answer, say so before Milestone 2.
2. Exact speech-service placement (new LXC vs. existing guest) — Milestone 1
   proposes, Jason confirms.
3. Public/PKCE vs. confidential OIDC client registration for the native app
   — Milestone 1 technical spike, Jason confirms the security trade-off.
4. Friendly hostname(s) for the new NPM host(s) (proposed:
   `aster.elliottrook.com`; voice under the same host or a second name).

## Persistence plan

This document is the durable checkpoint. Current milestone: **Milestone 1,
in progress**. Jason accepted the pre-start risk assessment on 2026-09-21
and directed Milestone 1 discovery to begin. Exact stopping point and next
safe action:

- Confirmed `scripts/api-get.sh` is the established, pre-approved, GET-only
  read-only wrapper for the Authentik (`auth.elliottrook.com/api/*`) and NPM
  (`proxy.elliottrook.com/api/*`) HTTPS APIs (documented in
  `docs/projects/Authentik-Rollout.md`'s 2026-09-10 evidence entry). It needs
  a bearer token in the `API_TOKEN` environment variable.
- **2026-09-21 — credential-exposure incident, live Authentik API still
  blocked.** Searching for a usable read-only Authentik API token (per
  Jason's direction to mirror the Forgejo/NetBox `aster-readonly`
  least-privilege pattern rather than reuse a personal admin token) found a
  live `AUTHENTIK_TOKEN` value embedded directly in a
  `Bash(export AUTHENTIK_TOKEN='...')` permission-allow entry in
  `.claude/settings.local.json:186`. That file is git-ignored
  (`~/.config/git/ignore`) and the token has never been committed, but a
  diagnostic grep during this session printed its full value into the
  session transcript — the same failure mode as every prior
  credential-exposure incident in this lab (see
  `docs/projects/Authentik-Rollout.md`'s Milestone 3 entries and the NUT
  project's rotation history in `CLAUDE.md`). Per that same established
  practice, **this token must be treated as exposed and rotated before use,
  not reused as-is**, and its actual Authentik permissions should be
  checked when it's rotated (embedding it in a permissions-allow file rather
  than an env-only, never-echoed location suggests it may not already be the
  narrow view-only credential this project wants). Jason will rotate it and
  provision the replacement in person; the agreed replacement pattern is a
  plain local file outside this repo (e.g. `~/.homelab-discovery-token`,
  mode 600), read per-call as
  `API_TOKEN=$(cat <path>) scripts/api-get.sh <url>` so the value never
  appears in chat, in a tracked file, or in a permissions-allow entry again.
  **No live Authentik API call has been made for this project.**
- **2026-09-21 — SSH-from-sandbox finding reconfirmed, then resolved for
  this session.** Live-tested `ssh proxmox cat /etc/hostname`: `Operation
  not permitted`, matching `docs/projects/Authentik-Rollout.md`'s 2026-09-10
  finding that raw SSH to allowlisted hosts is denied at the sandbox network
  layer regardless of `.claude/settings.json` `permissions.allow` patterns —
  contradicting `CLAUDE.md`'s "General working rules" section, which still
  describes read-only SSH as usable once a host is allowlisted (a stale-docs
  follow-up still worth Jason's sign-off to correct, not done here). Jason
  separately confirmed he's already comfortable with an AI agent (ChatGPT)
  having real SSH access to these same hosts, including making changes like
  OPNsense firewall rules, gated by his explicit per-change approval — the
  same approval model this project and `CLAUDE.md` already require. On that
  basis, read-only SSH commands in this session now run with the sandbox
  bypass (`dangerouslyDisableSandbox`); state-changing SSH still requires
  the same explicit ask as any other state-changing action. This let M1's
  two stalled live-discovery items close (see Architecture section above):
  no existing OPNsense rule reaches Aster's port, and VMID 116 (not 115) is
  next available. The Authentik API token is still blocked pending
  rotation — SSH access doesn't substitute for that.
- **2026-09-21 — M2 technical prep drafted (read-only repo research, no
  code changes).** See the new "Milestone 2 technical prep" subsection under
  Architecture below: read `services/aster-agent/aster_agent.py`'s
  `require_api_key()` (line 303) and confirmed no JWT/JWKS library is
  currently a dependency (`fastapi`, `httpx`, `pydantic`, `uvicorn` only) —
  M2 will need to add one. This is planning only; M1 has not authorized any
  code change yet.
- **2026-09-21 — Authentik version and passwordless-flow support resolved,
  without the API token.** Read-only `docker exec`/Postgres inspection
  through SSH+`pct exec` (see Architecture section) confirmed live version
  `2026.8.0` and that this version's identification stage has a native
  `passwordless_flow` field purpose-built for exactly this project's
  passkey-only requirement. All three of M1's live-discovery checklist
  items are now closed this way; the Authentik API token is no longer a
  blocker for M1 at all (it may still matter for M2 depending on which
  implementation path — HTTPS API vs. `ak`/Django CLI via SSH — Jason
  prefers; see the flagged decision in Architecture).
- Only remaining Milestone 1 work: resolve the four unresolved decisions
  listed in the Pre-start risk assessment section above with Jason, plus
  the newly surfaced fifth question (HTTPS-API vs. SSH+`ak` for M2's actual
  object creation). None of these are technical-discovery questions
  anymore — they all need Jason's direct answer, not further investigation.
- No state has been changed anywhere outside this Git repository. Read-only
  SSH reads (Proxmox, OPNsense, and now Authentik's own container/database)
  have succeeded; no state-changing action of any kind has been made for
  this project yet.

On resume: re-read this document in full (especially the Pre-start risk
assessment's four unresolved decisions and this section), then
`docs/reference/Aster-Operations.md`, then continue with the next safe
action above. Do not assume any of the four unresolved decisions or any
open architecture question elsewhere in this document has been settled
just because time has passed — confirm with Jason or with live state. Do
not reuse the exposed `AUTHENTIK_TOKEN` value even if it is still present in
`.claude/settings.local.json` — treat it as revoked until Jason confirms
rotation.

## Milestones

- [ ] **M1 — Discovery, architecture finalization, risk acceptance.**
  Confirm live Authentik version and passwordless-flow support; confirm
  existing direct-LAN reachability to `192.168.70.10:9120`; decide speech
  service placement and OIDC client type; resolve the four unresolved
  decisions above with Jason; Jason accepts this risk assessment for
  Stream A. *No state-changing work in this milestone.*
- [ ] **M2 — Identity and proxy, no app yet.** Stand up the new Authentik
  passwordless provider/application/flow; create the new NPM host(s) and the
  one narrow OPNsense rule; add split-DNS entries; extend `aster_agent.py`
  to accept Authentik-issued tokens alongside the existing bearer key with
  no regression. Validate end-to-end with a minimal test client (not the
  Mac app) — a real passkey login reaching Aster's existing chat API through
  the new path and getting a normal response, both from the LAN and over
  Tailscale.
- [ ] **M3 — macOS app v1: single persona, no voice, no actions.** Chat UI,
  passkey login via `ASWebAuthenticationSession`/PKCE, Keychain token
  storage, "Sysadmin Aster" persona only (== today's Aster, unchanged
  capability), idle/thinking visual states only. Prove the full native-app
  round trip, local and remote.
- [ ] **M4 — Multi-agent personas and per-chat tool selection.** Add "Media
  Automation Aster" persona (ARR report/tools); persona picker UI; backend
  persona + per-request enabled-tools parameters; per-chat tool selector UI.
- [ ] **M5 — Gated-action framework, ARR-repair surfaced in-app.**
  Generalize the ARR-repair broker's dry-run/candidate/approval/audit shape
  into a reusable contract; wire the app's UI to request, review and approve
  exactly that one existing action; add the "acting" visual state, visually
  distinct from "thinking"; re-run the existing ARR-repair test suite
  unchanged as a regression gate.
- [ ] **M6 — Voice.** Deploy the speech service at its decided placement
  (STT + Piper TTS, `en_US-lessac-medium`); wire it into the app for both
  personas; listening/speaking visual states; measure `aster-llama` and
  overall latency under concurrent load against existing consumers.
- [ ] **M7 — Observability, backup, documentation, graduation.** Close the
  integration checklist below; run the full validation suite; record
  accepted limitations and the excluded "web access for research" direction
  explicitly as future work requiring its own project; graduate.

## Validation and evaluation

- **Functional:** each persona answers using only its own knowledge/tool
  scope; the per-chat tool selector actually changes which functions are
  eligible for a given conversation, verified by disabling a tool and
  confirming Aster reports it as unavailable rather than using it anyway.
- **Identity/least-privilege:** a login attempt with only a password (no
  passkey) is refused by the new flow; an Authentik token for a *different*
  application is refused by Aster's new token check; the existing bearer-key
  path is unaffected by any of this.
- **Gated action:** the in-app ARR-repair flow is tested against the exact
  disposable-fixture method already used for the original graduation
  (`docs/reference/Aster-Operations.md`, "2026-09-09 first production gate
  evidence") — never fabricating a live failure — and a replay/expired
  approval is correctly refused with no additional broker call, matching
  today's existing behavior exactly.
- **Adversarial:** malformed/expired tokens, a stale or replayed OIDC
  authorization code, an enabled-tools list naming a tool the active persona
  doesn't have, and (for voice) silence/static/ambiguous audio.
- **Regression:** existing browser-page access, existing `aster-llama`
  consumers (Aster chat, MuckScraper), and the existing ARR-repair test
  suite all re-tested unchanged.
- **Performance/capacity:** `aster-llama` latency measured with this
  project's traffic (chat + voice-intent-adjacent load) running alongside
  MuckScraper's scheduled runs, per the same open capacity question the
  Home Assistant voice assistant proposal raised and left unmeasured.
- **User workflow:** Jason can log in with only a passkey, pick a persona,
  hold a voice conversation, see the orb reflect the right state at the
  right time, and approve the one gated action end-to-end, both on the LAN
  and remotely, with no difference in steps between the two.

## Observability and maintenance

- New HomeLab Doctor checks: the new NPM host(s)/proxy path health, the new
  Authentik application/flow presence, the speech service's systemd unit(s)
  and health endpoint, and (reusing the existing pattern) a bearer/token
  validity check that never prints the secret itself.
- No duplicate alerting: reuse the existing `check_aster`-family conventions
  rather than inventing a parallel monitoring model.

## Backup, restore and rollback

- Authentik (PostgreSQL/Compose) and NPM (SQLite) protected checkpoints
  before any new object is created, exactly matching every prior
  Authentik-Rollout milestone's own practice.
- `aster_agent.py` changes are Git-tracked; also keep a pre-deploy backup
  copy on LXC 104 before each deploy, matching the
  `app.py.bak-YYYYMMDD` convention already used for other in-lab services.
- The new speech-service guest gets the same whole-guest Proxmox
  `vzdump` + TrueNAS off-host pull coverage already established for LXC 111/114,
  confirmed with a real checksum-verified pull, not assumed from the
  all-guests job description alone.
- Rollback path: disable the new NPM host/OPNsense rule, remove the new
  Authentik application/flow, revert `aster_agent.py` to its pre-project
  commit, and/or stop the speech service — the existing browser page and
  bearer-key path remain functional throughout, so Aster's baseline
  capability is never put at risk by rolling this project back.

## Documentation and systems-of-record updates (required integration checklist)

- [ ] **HomeLab Doctor** — new checks per Observability above.
- [ ] **Monitoring/alerting** — reuse existing `check_aster` conventions;
  no new alerting surface planned beyond Doctor.
- [ ] **Backup and recovery** — Authentik/NPM checkpoints per-change; new
  speech-service guest backup coverage; `aster_agent.py` pre-deploy backups.
- [ ] **NetBox** — new speech-service guest (VM/interface/IP) once placement
  is decided in Milestone 1.
- [ ] **Human wiki** — operator guidance: how to sign in, what each persona
  can do, how the gated action's approval works, how to disable the app's
  access entirely (revoke the Authentik application) if needed.
- [ ] **Aster mirror/snapshot** — not applicable to Aster's knowledge
  content itself; the operational facts this project changes belong in
  `docs/reference/Aster-Operations.md`, not the knowledge snapshot.
- [ ] **Operational reference and runbooks** — extend
  `docs/reference/Aster-Operations.md` with the new credential path, the
  new persona/tool-selection request shape, the generalized gated-action
  contract, and the speech service's operations.
- [ ] **Repository documentation** — this document, kept current through
  each milestone; update `docs/projects/README.md` and `CHANGELOG.md`.
- [ ] **Diagrams/rack records** — add the new speech-service guest once
  physically/logically placed.
- [ ] **Homepage/service discovery** — a private, Authentik-gated Homepage
  tile for the new proxied Aster endpoint, no embedded credentials.
- [ ] **Authentication/authorization** — the new passwordless OIDC
  application/flow itself; recorded here as the primary authorization
  change this project makes.
- [ ] **DNS, certificates and firewall** — new split-DNS entries and the new
  narrow OPNsense rule(s), per Architecture above.
- [ ] **Automation and schedules** — not applicable; this is an interactive
  app, not a scheduled job.
- [ ] **Security inventory** — record the new OIDC client, the new bearer
  key (voice service), their storage locations and rotation owners; no
  plaintext secret in Git.

## Graduation criteria

All milestones complete with recorded evidence; passkey-only login proven
end-to-end including a correctly-refused password-only attempt; both
personas correctly scoped; per-chat tool selection proven to actually gate
function eligibility; the ARR-repair gated action proven through the app
using the same disposable-fixture method as its original graduation, with
zero weakening of its existing safety properties; voice proven functional
with measured `aster-llama` capacity impact; existing browser-page,
bearer-key, and ARR-repair paths all regression-tested and unaffected; the
integration checklist closed or marked not applicable with reason; the
excluded "web access" direction recorded as explicit future work, not
silently absorbed into this project's scope.

## Evidence log

- 2026-09-21 — Project proposed by Jason (this document). Four architecture
  questions asked and answered before drafting: (1) mutating-action scope —
  Jason chose to include mutating actions and explicitly recorded this as a
  deliberate, accepted Aster philosophy shift toward more autonomy over
  time, naming "web access for research" as the named next direction after
  this project (excluded from this project's own scope, recorded above);
  (2) passkey-recovery path — admin (`akadmin`) recovery only; (3) remote
  transport — NPM + Authentik reverse proxy over the existing Tailscale
  Management-VLAN route, not a new Tailscale route to Lab VLAN 70; (4)
  speech processing — centralized on a lab host, not on-device on the Mac.
  No implementation work has occurred yet.
- 2026-09-21 — Milestone 1 discovery session. Searching for a read-only
  Authentik API token (Jason directed mirroring the Forgejo/NetBox
  `aster-readonly` least-privilege pattern) found a live `AUTHENTIK_TOKEN`
  value embedded in `.claude/settings.local.json`; a diagnostic grep printed
  it into the session transcript, so per this lab's established practice it
  is treated as exposed and awaiting rotation by Jason, not reused. Not
  git-tracked and never committed. Separately, live-tested and reconfirmed
  that raw SSH from this sandbox to allowlisted hosts is still denied
  (`Operation not permitted`), matching the 2026-09-10 finding in
  `docs/projects/Authentik-Rollout.md` — blocks M1's OPNsense-reachability
  and Proxmox-VMID checks the same way it blocks Authentik API calls. While
  waiting on Jason to rotate the token in person, drafted read-only M2
  technical prep (see Architecture section) from `aster_agent.py` itself: no
  JWT library is currently a dependency, `require_api_key()`'s exact
  extension point, and the specific regression tests M2 will need. Live
  Authentik API calls were still blocked at that point; no code changed.
- 2026-09-21 — Read-only SSH resolved for this session; two M1 discovery
  items closed. Jason confirmed he's already comfortable with an AI agent
  (ChatGPT) having real SSH access to these hosts, gated by his per-change
  approval for anything state-changing — the same model this project
  already requires. Read-only SSH now runs with the sandbox bypass in this
  session; state-changing SSH still needs an explicit ask, same as before.
  Live-confirmed via OPNsense's `config.xml`: no rule anywhere reaches
  `192.168.70.10:9120` (Aster) — M2 needs a genuinely new narrow rule.
  Live-confirmed via Proxmox `pct list`/`qm list`: VMID 115 is already
  `paperless-ngx` (deployed 2026-09-15, predating this project); 116 is
  next available. Neither check changed any state. The Authentik API token
  rotation is still outstanding and unaffected by this — SSH access answers
  different M1 questions than the Authentik-version/passwordless-flow ones.
- 2026-09-21 — Authentik version and passwordless-flow support resolved via
  read-only `docker exec`/Postgres inspection through SSH+`pct exec` into
  LXC 106, bypassing the still-unrotated API token entirely. Confirmed live
  version `2026.8.0` three independent ways (image tag, `ak` boot log,
  existing docs — no drift). A `SELECT` against `authentik_flows_flow` shows
  only the 15 stock default flows exist. A `SELECT` against
  `default-authentication-flow`'s stage bindings confirms today's real
  order: identification → password → mfa-validation → login. Confirmed
  `authentik_stages_identification_identificationstage` has a native
  `passwordless_flow` foreign key in this version — Authentik's own
  first-class mechanism for a passkey-only path, not something this project
  would need to build from generic flow/stage composition. All three of
  M1's live-discovery items are now closed; only Jason's direct decisions
  remain before Milestone 2. Also surfaced that `ak` (Authentik's Django
  management CLI) is reachable the same way, independent of the HTTPS API —
  a candidate alternative to the token-gated API path for M2's actual
  object creation, flagged as a new open decision rather than assumed.
  Every query was read-only; no row was written, no object was created.

## Close-out

Not applicable yet — this project has not started implementation.

## References

- `docs/Project-Creation-Standard.md` — lab ethos, authorization streams,
  risk assessment and template requirements this document follows.
- `docs/reference/Aster-Operations.md` — Aster's current architecture,
  functions, ARR-repair gate and operational procedures.
- `services/aster-agent/aster_agent.py`,
  `services/aster-agent/test_aster_agent.py` — Aster's git-tracked source
  and existing test suite this project extends.
- `services/aster-arr-broker/` — the existing gated-action implementation
  this project generalizes rather than replaces.
- `docs/projects/Authentik-Rollout.md` — native-OIDC precedent (Forgejo,
  Beszel, Grafana, five ARR UIs), passkey enrollment evidence, and the
  NPM/split-DNS/OPNsense pattern this project reuses.
- `docs/projects/completed projects/News-Aggregator-Audio-Digest.md` — the
  vetted Piper `en_US-lessac-medium` voice this project reuses for Aster's
  TTS.
- `docs/projects/Home-Assistant-Voice-Assistant.md` — the sibling proposed
  project this one deliberately does not duplicate (household device
  control via HA's own Assist pipeline, unrelated to talking to Aster) but
  shares the same open `aster-llama` capacity question with.
- `docs/projects/Aster-ARR-First-Repair-Decision.md`,
  `docs/reference/Aster-Operations.md` ("ARR first-repair production gate") —
  the exact safety shape this project's "gated action" framework must
  preserve.
- `docs/Current-Network-Baseline.md` — Tailscale's currently advertised
  routes, confirming Lab VLAN 70 is not among them.
