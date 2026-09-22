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

## Visual identity

The accepted app-icon concept combines the two meanings behind the Aster name:
an aster flower and the Greek-root idea of a star. Eight subdued indigo/violet
petals surround a warm central orb, tying the identity to the app's planned
voice-state indicator. The four cardinal petals carry a deliberately light
compass-needle treatment, adding guidance and orientation without turning the
mark into a literal compass rose. The source artwork is retained at
[`docs/assets/aster-companion/aster-app-icon-concept-v2-compass.png`](../assets/aster-companion/aster-app-icon-concept-v2-compass.png).

![Accepted Aster Companion app-icon concept](../assets/aster-companion/aster-app-icon-concept-v2-compass.png)

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
- **A web client (added to scope 2026-09-22), the actual "works on my
  phone" answer** — not native iOS, which Jason decided against (see
  Exclusions) since a real install without a paid Apple Developer
  membership expires weekly. Runs in Mobile Safari (and any other
  browser — Android, another Mac), installable to the home screen for an
  app-like launch. Uses the same passkey login as the macOS app, just via
  ordinary browser-redirect OAuth2/PKCE instead of
  `ASWebAuthenticationSession` — WebAuthn/passkeys are native to Mobile
  Safari already, proven working manually against this exact flow during
  M2's live testing, so nothing about the passkey experience is weaker,
  only where the resulting token is stored (see Exclusions' security note
  once this is built).
- Authentik login using a new, dedicated passwordless (passkey-only) OIDC
  flow and application, via the system browser (`ASWebAuthenticationSession`
  for the macOS app; ordinary redirect-based OAuth2/PKCE for the web
  client) and PKCE, with the resulting token stored in the macOS Keychain
  (macOS app) or browser storage (web client).
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
  **Confirmed 2026-09-22: voice targets both the macOS app and the web
  client when M6 is built, not just one** — a browser can do microphone
  capture and audio playback natively, so this isn't a web-client
  limitation, just something to design for both from the start rather
  than bolt onto the web client later.
- A visual state indicator (orb/EQ-style graphic) with distinct idle,
  listening, thinking, speaking and acting states — "acting" must be visually
  unmistakable from "thinking," since one of them may mutate state and the
  other never does. Built once as shared design intent, implemented per
  client (native `OrbView` in the macOS app, its web equivalent in the
  web client).

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
- Native iOS/iPadOS builds. **Decided against 2026-09-22**, not just
  deferred: a real iOS install without a paid Apple Developer Program
  membership ($99/year) expires after 7 days and needs Xcode +
  a physical/wireless USB pairing with a Mac to refresh — Jason has no
  interest in that subscription. A web client (see Scope above) is the
  actual answer to "works on my phone" instead; see the Evidence log entry
  explaining that choice.
- Windows/Linux desktop clients.
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

This document is the durable checkpoint. Current milestone: **Milestone 3,
in progress** (M1 and M2 are complete — see the Milestones checklist and
the end of the Evidence log below for tonight's 2026-09-21 stopping point
and exactly what's left in M3). Jason accepted the pre-start risk
assessment on 2026-09-21 and directed Milestone 1 discovery to begin.
Below is that discovery's original, still-accurate narrative:

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

*(The paragraph above and the entries immediately following it are the
original Milestone 1 discovery narrative, left as written at the time —
by the time you're reading this, M1's four unresolved decisions are long
since resolved, per the Milestones checklist. The `AUTHENTIK_TOKEN`
exposure this section describes is also resolved: M2 ended up not needing
that token at all, since Authentik object creation went through `ak`/SSH
instead — see the M2 evidence log entries. It's still good practice to
rotate that token whenever convenient, but nothing in this project is
blocked on it.)*

**On resume today (2026-09-21 session end): re-read the Evidence log's
last few entries (from "Heavier query succeeded through the app..."
backward) and the M3 Milestones checklist item, not this section — this
section is Milestone 1 history.** In short: M1 and M2 are fully complete
and pushed to `origin`/GitHub. M3's native macOS app
(`apps/AsterCompanion`) is built, running, and has proven a full real
passkey-login-to-chat-reply round trip on the LAN, including a heavier
`lab doctor`-style query. What's left before M3 itself can close:
1. Repeat the same real native-app round trip over Tailscale (only the
   manual-URL stand-in was tested over Tailscale in M2, not the actual
   app).
2. Decide whether to open the app in Xcode / set up a stable local code
   signing identity — right now it's ad-hoc signed and rebuilt via
   `apps/AsterCompanion/build-app.sh`, which means Keychain re-prompts
   for permission on every rebuild (harmless, just repetitive during
   active iteration).
3. `git commit`/`git push` are current as of this session's end — check
   `git log` and `git status` before assuming so, per this document's own
   evidence-log discipline, rather than trusting this note indefinitely.

## Milestones

- [x] **M1 — Discovery, architecture finalization, risk acceptance.**
  **Complete 2026-09-21.** Live Authentik version (`2026.8.0`) and
  passwordless-flow support confirmed (native `passwordless_flow` field on
  the identification stage). Confirmed no existing rule reaches
  `192.168.70.10:9120` — no direct-LAN path to retire. Decisions with
  Jason: (1) mutating-action scope stays ARR-repair-only for now; (2)
  speech service gets its own new dedicated LXC (VMID 116) and its own
  hostname, not the news aggregator's guest, since Jason wants Home
  Assistant and future clients to consume it too and it's TTS-only/trial
  today; (3) native app registers as a public OIDC client with PKCE, no
  embedded secret; (4) M2's Authentik object creation goes through SSH +
  `ak` (Django management CLI), not the token-gated HTTPS API — the
  `AUTHENTIK_TOKEN` exposure earlier is moot for this project either way,
  though still worth rotating for hygiene. No state was changed in this
  milestone.
- [x] **M2 — Identity and proxy, no app yet. Complete 2026-09-21.** Stood
  up the new Authentik passwordless provider/application/flow; created the
  new NPM host and the OPNsense rule; added split-DNS entries; extended
  `aster_agent.py` to accept Authentik-issued tokens alongside the existing
  bearer key with no regression. Validated end-to-end with a minimal test
  client (not the Mac app) — a real passkey login reaching Aster's existing
  chat API through the new path and getting a normal response, **both from
  the LAN and over Tailscale**, both with real tokens from real passkey
  logins, not simulated. Two genuine gaps were found and fixed along the
  way, neither of them Aster-specific scope creep — both were real
  requirements of "works both locally and remotely" that hadn't been
  exercised before: (1) Aster's own host had no firewall path to reach
  Authentik's JWKS at all (new egress rule, permanent); (2) Tailscale's
  split-DNS was scoped to the `internal` namespace only, never extended to
  `elliottrook.com` — a tailnet-wide gap affecting every app on that
  domain, not just Aster, fixed by Jason adding the domain to Tailscale's
  DNS settings.
- [x] **M3 — macOS app v1 + web client v1: single persona, no voice, no
  actions. Complete 2026-09-22.** Chat UI, passkey login, Keychain (macOS)
  or browser-storage (web) token storage, "Sysadmin Aster" persona only
  (== today's Aster, unchanged capability), idle/thinking visual states
  only. Prove the full round trip, local and remote, for both clients.
  - **macOS app: LAN round trip proven 2026-09-21** with a real
    interactive passkey login and real chat replies (including a heavier
    `lab doctor`-style query) through the actual running app, not a
    stand-in. Visual design (icon + `OrbView`) iterated to something Jason
    is happy with. **Accepted gap, not fixed:** the same round trip
    hasn't been separately repeated over Tailscale (only the manual-URL
    test from M2 was) — Jason's explicit call 2026-09-22, since the web
    client now covers "works on my phone" more completely than native
    iOS would have, making this not worth chasing further. The app is
    also still an unsigned ad-hoc-built `.app` run directly from
    `.build/`, not yet in Xcode or set up for a stable local signing
    identity (every rebuild currently re-triggers the macOS Keychain
    permission prompt — cosmetic during active development, not fixed,
    not blocking).
  - **Web client: built and proven complete 2026-09-22, both LAN and
    Tailscale.** Native iOS was decided against, not deferred (see
    Exclusions) — a real install without a paid Apple Developer Program
    membership expires weekly, and Jason has no interest in that
    subscription. `GET /companion` in `aster_agent.py` is the actual
    "works on my phone" answer instead: real passkey/WebAuthn login via
    ordinary redirect-based OAuth2/PKCE (no `ASWebAuthenticationSession`
    equivalent needed in a browser), the same accepted orb artwork with an
    equivalent idle/thinking pulse via CSS, and streamed chat replies.
    Real bugs caught and fixed live, not assumed away: a heavier query hit
    real nginx `499`s ("client closed the connection") from iOS Safari
    killing the in-flight request while backgrounded — confirmed in NPM's
    own logs, not guessed — fixed by switching to the SSE streaming path
    `aster_agent.py` already had (first bytes arrive almost immediately
    instead of waiting for the whole reply). **Both the LAN and Tailscale
    round trips are now confirmed fully working**, end to end, including
    the streamed replies.
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
  (STT + Piper TTS, `en_US-lessac-medium`); wire it into **both the macOS
  app and the web client** (confirmed in scope for both 2026-09-22, not
  just the macOS app — a browser can do microphone capture and audio
  playback natively) for both personas; listening/speaking visual states
  on both clients; measure `aster-llama` and overall latency under
  concurrent load against existing consumers.
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
- 2026-09-21 — **Milestone 1 closed.** Jason confirmed all four pre-start
  decisions plus the fifth (M2 access path) surfaced during discovery: ARR-
  repair-only scope stands; speech service gets a new dedicated LXC (VMID
  116) with its own hostname rather than the news aggregator's guest, since
  Jason wants Home Assistant and future clients to consume it and today's
  news-aggregator TTS is trial-only/TTS-only; public OIDC client with PKCE;
  M2's Authentik object creation goes through SSH + `ak`, not the
  token-gated API.
- 2026-09-21 — **Milestone 2 started.** Took the same pre-change checkpoint
  every prior Authentik-Rollout milestone took before creating anything:
  `docker exec`'d a `pg_dump -Fc` of Authentik's database from inside LXC
  106 (`/opt/authentik/backups/authentik-before-aster-companion-20260921.dump`,
  root-only 0600, verified enumerable via `pg_restore -l` — 1807 TOC
  entries) plus a compose-file checkpoint, and an online SQLite backup of
  NPM's database from inside LXC 107 via Python's `sqlite3` module (safe
  under concurrent writes, unlike a plain file copy) to
  `/opt/nginx-proxy-manager/backups/database.before-aster-companion-20260921.sqlite`
  (root-only 0600, `PRAGMA integrity_check` returned `ok`). Both match the
  exact naming/permission convention already used for every prior milestone
  in that directory. No Authentik or NPM object has been created or
  modified yet. Next concrete step: create the new `aster-companion`
  passwordless flow and its stages (identification → webauthn → login, no
  password) — paused to flag the implementation choice first: Authentik's
  own declarative blueprint mechanism (`ak apply_blueprint`) is the
  idiomatic, safer way to create this, but this deployment doesn't
  currently mount a blueprints directory, so using it means a small compose
  change first; the alternative is a direct `ak shell` Django-ORM script
  against only the new objects, no compose change needed, but more
  hand-rolled. Flagging rather than picking silently, since it's a real
  risk-profile difference, not just a style preference.
- 2026-09-21 — **New Authentik flow created via blueprint.** Jason chose
  blueprints. Rather than a permanent compose/volume change, discovered
  `ak apply_blueprint` resolves paths relative to Authentik's existing
  `/blueprints/` directory (already present in the image, no mount
  needed), so the blueprint file was `docker cp`'d directly into the
  running `authentik-worker-1` container instead. Before writing it,
  cross-checked field/model names against Authentik's own shipped
  reference (`/blueprints/example/flows-login-2fa.yaml`) rather than
  trusting the earlier schema archaeology alone — this caught a real
  mistake in the first draft (`stage` belongs inside a
  `flowstagebinding`'s `identifiers`, not `attrs`) before anything was
  applied. Ran `--dry-run` clean twice, then applied for real.
  Read-only verification after: exactly one new flow,
  `aster-companion-passwordless` (16 flows total, was 15), with stages
  bound in order 10 (identification) → 20 (`authenticatorvalidatestage`
  restricted to `device_classes: [webauthn]` only, `not_configured_action:
  deny`, `webauthn_user_verification: required`) → 100 (login) — no
  password stage anywhere in it. `default-authentication-flow` re-checked
  and confirmed byte-for-byte unchanged (still the same 4 stages, same
  order) — nothing shared was touched. The blueprint source is committed
  at `services/authentik-blueprints/aster-companion-passwordless-flow.yaml`
  as the real source of truth: applying it registered a `BlueprintInstance`
  tracking row in Authentik's own database, but the file itself only lives
  in the container's writable layer (no host volume mount), so it would be
  lost if the Authentik containers are ever recreated (not just restarted)
  — the git copy is the durable record; the created flow/stage rows
  themselves are safe either way since they're in Postgres, which is
  backed up.
- 2026-09-21 — **`aster-companion` OAuth2 provider and application
  created.** Before writing this blueprint, checked Authentik's own field
  documentation via `ak shell` rather than assume — this caught a real
  misunderstanding: `Provider.authorization_flow` is the **consent** flow
  (every existing provider here points it at
  `default-provider-authorization-explicit-consent`), not the login flow.
  The actual per-app login override is `Provider.authentication_flow`
  ("Flow used for authentication when the associated application is
  accessed by an un-authenticated user" — Authentik's own help text). Had
  this gone unchecked, the new passwordless flow would have been wired to
  the wrong hook and never actually run. Also found and used
  `/blueprints/testing/oidc-conformance.yaml`, a complete shipped
  provider+application blueprint example, to confirm exact syntax
  (`!Find [app.model, [field, value]]` for referencing existing objects,
  the plain-list `redirect_uris` structure) instead of guessing — and
  deliberately used the *real* default property mappings
  (`goauthentik.io/providers/oauth2/scope-profile`, returning actual user
  data) rather than that file's `scope-profile-oidc-standard` mapping,
  which fills placeholder fields like `"website": "foo"` for conformance
  testing only. Dry-ran clean, applied, then verified every field
  read-only: `client_type: public`, `client_id: aster-companion`,
  `authentication_flow: aster-companion-passwordless` (the new flow),
  `authorization_flow: default-provider-authorization-explicit-consent`
  and `invalidation_flow: default-provider-invalidation-flow` (matching
  existing convention), `redirect_uris` set to the provisional
  `aster-companion://callback` custom URL scheme (placeholder pending the
  actual app's bundle ID/scheme in M3 — trivially changed later, it's just
  a field on the provider), `grant_types: [authorization_code,
  refresh_token]`, and exactly the intended 4 property mappings (openid,
  email, profile, offline_access). Provider count went 17→18. The
  application (`slug: aster-companion`) is linked to it, with exactly one
  enabled `PolicyBinding` directly to user `jason` (order 0) — matching
  the exact "one direct owner binding" pattern already used for
  Forgejo/Grafana/Portainer/the five ARR apps. Blueprint source committed
  at `services/authentik-blueprints/aster-companion-provider-app.yaml`,
  same durability note as the flow blueprint (container-local file, DB
  rows are the safe part). Next step: the new NPM host for
  `aster.elliottrook.com` and the one narrow OPNsense rule to reach
  `192.168.70.10:9120` — Authentik's side of M2 is now functionally
  complete pending live login testing, which needs the proxy path to
  exist first.
- 2026-09-21 — **New NPM host created for `aster.elliottrook.com`.** NPM
  has no declarative/CLI equivalent to Authentik's blueprints, and its own
  admin API needs a login token we don't have — but hand-writing the nginx
  conf directly was ruled out as too risky (one syntax error there can fail
  `nginx -t` for the whole reload, taking every proxied host in the lab
  down, not just this one). Instead, read NPM's own internal application
  code (`/app/internal/proxy-host.js`, `/app/internal/nginx.js` inside the
  `nginx-proxy-manager` container) and called its internal
  `internalNginx.configure()` directly via a small script executed with
  `docker exec ... node` — the same safe, tested path NPM's own UI uses
  (test config → generate → test again → only then reload; rolls back
  automatically if the test fails), just invoked without going through the
  HTTP/auth layer. Modeled the new row on the existing `git.elliottrook.com`
  (Forgejo) entry — same certificate (id 8, the existing wildcard), same
  TLS/HTTP2/websocket/exploit-blocking settings, plain reverse proxy with
  no forward-auth `advanced_config` (Aster does native OIDC, not
  NPM-forward-auth, matching Forgejo/Grafana's pattern not
  Homepage/Beszel's). First attempt exposed a real gap: NPM's real
  `create()` re-fetches the row with `certificate`/`owner`/`access_list`
  eager-loaded before generating the config, which my script skipped —
  the template's SSL block is gated on the *expanded* `certificate`
  relation object, not just the `certificate_id` FK, so the first version
  silently produced a config with no `listen 443 ssl` block at all
  (caught by testing the live vhost directly against the container with
  correct SNI via `curl --connect-to`, not by assuming success from the
  "no errors" script output). Fixed by re-fetching with
  `.withGraphFetched("[certificate,owner,access_list.[clients,items]]")`
  before calling `configure()` again. Verified after the fix: SSL block
  present, certificate correctly resolved to `*.elliottrook.com`, and a
  live test now reaches nginx and gets a `504` timing out trying to reach
  `192.168.70.10:9120` — the expected, correct result at this stage, since
  the OPNsense path there doesn't exist yet (confirmed absent in M1). All
  17 pre-existing hosts re-checked healthy (`nginx_online: true`) both
  before and after — the reload didn't disturb anything else. New host is
  id 18 in `proxy_host`.
- 2026-09-21 — **OPNsense rule created for NPM → Aster; full path verified
  end-to-end.** OPNsense's real rule storage in this version (26.7.1) is
  not the near-empty legacy `<filter>` block — a `count()` sanity check
  during discovery (only 2 rules found via the classic `config_read_array`
  helper, when dozens plainly existed on-screen) caught this before any
  write happened. All real rules, including every existing precedent this
  project needs to match, live under `<OPNsense><Firewall><Filter>` — the
  newer MVC-managed model. Followed
  `/usr/local/opnsense/scripts/auth/add_user.php` (a real shipped OPNsense
  script) as the reference pattern: `legacy_bindings.inc` bootstrap,
  `Config::getInstance()->lock()`, instantiate `\OPNsense\Firewall\Filter`,
  `Add()` a node, set fields directly, `performValidation()` scoped to the
  new node, save only if clean. Matched every field to the closest existing
  precedent (`Allow NPM to Homepage`, `192.168.50.23 → 192.168.20.20:3000`
  on interface `opt4`, confirmed via the interfaces section to be
  Management VLAN 50's real identifier — not assumed): same interface,
  same action/quick/statetype, source `192.168.50.23`, destination changed
  to `192.168.70.10:9120`. Took a root-only pre-change config backup first
  (`/conf/backup/config-aster-companion-before-20260921.xml`, XML-validated)
  and ran a true dry-run (validate-only, always unlocking, never saving)
  before the real write, matching the discipline used for Authentik/NPM.
  **First application reload succeeded cleanly but the path still didn't
  work** — a live NPM→Aster test returned the same `504` as before the
  rule existed. Diagnosed by checking Aster's own health directly from
  Proxmox first (confirmed healthy — ruled out the backend), then reading
  the live compiled ruleset (`pfctl -sr`) rather than trusting the "OK"
  save result: the new rule had landed *after* an existing
  `block drop ... to <RFC1918_Networks>` catch-all on the same interface
  (sequence `2200`), because the picked sequence value (`3200`, based only
  on this config's overall maximum) put it on the wrong side of that block
  — every other narrow allow rule on this interface sits just under `2200`
  for exactly this reason, which wasn't obvious until the compiled rule
  order was actually inspected. Fixed by updating the existing rule's
  `sequence` to `2199` (between the `2196` neighbor and the `2200` block)
  and reloading again. **Verified after the fix:** `pfctl -sr` shows the
  rule at line 215, the block at line 218 (correct order); a live request
  through the full chain (NPM → OPNsense → Aster) returns the genuine
  `{"status":"ok","service":"aster-agent"}` from Aster's own health
  endpoint, not a proxy-layer response; rule count is 69 (was 68, no
  duplicate left over from the fix); `git.elliottrook.com` and
  `auth.elliottrook.com` still return correctly through NPM; the
  pre-existing Homepage rule is untouched. Authentik → NPM → OPNsense →
  Aster is now a fully working path end-to-end, reachable at
  `aster.elliottrook.com` once DNS exists. Remaining M2 work: split-DNS
  entries (OPNsense Unbound + both Pi-holes) and extending
  `aster_agent.py` to accept Authentik-issued tokens alongside the
  existing bearer key.
- 2026-09-21 — **Split-DNS added on all three resolvers; full path
  verified end-to-end from a real client.** Primary Pi-hole (`dns1`,
  `pihole/pihole:2026.05.0` in Docker on LXC 100) and secondary Pi-hole
  (`dns2`, `pihole/pihole:2026.07.2` in a TrueNAS app,
  `ix-pihole-pihole-1`) both store local DNS records in a `dns.hosts`
  array inside `pihole.toml`, applied live via the official
  `pihole-FTL --config dns.hosts '[...]'` CLI (no file editing, no
  restart needed — took effect immediately, confirmed via `dig` against
  each Pi-hole directly). Read each array back first and appended to the
  real existing 17 entries programmatically rather than retyping them, to
  avoid a transcription error wiping out someone else's entry. OPNsense's
  Unbound needed the same model-based approach as the firewall rule:
  `\OPNsense\Unbound\Unbound`, `hosts.host`, matching the existing `auth`
  host override's exact fields (`rr: A`, `addptr: 1`). Dry-ran clean,
  applied, then found resolution didn't take effect until an explicit
  `configctl unbound restart` (no incremental "reload" action exists for
  this service, unlike the firewall) — checked this rather than assuming,
  by testing resolution immediately after the config save and getting an
  empty answer section. After the restart, `drill` against Unbound
  confirms the correct answer and `auth`/`git` still resolve correctly
  (no regression); Unbound remained running throughout with no reported
  errors. **Final verification, from this Mac, using genuine DNS
  resolution with no test harness or `--connect-to` trick** (the same
  path any real client on the network would take):
  `curl https://aster.elliottrook.com/health` resolves to `192.168.50.23`
  and returns `{"status":"ok","service":"aster-agent"}` — Aster's own
  response, through Authentik-ready NPM, through the new OPNsense rule,
  to Aster itself. **Every infrastructure piece of Milestone 2 is now
  live and verified except the code change.** Only remaining M2 item:
  extend `aster_agent.py` to accept Authentik-issued tokens alongside the
  existing bearer key, with no regression to the existing browser page.
- 2026-09-21 — **`aster_agent.py` extended to accept Authentik tokens;
  fully tested, not yet deployed.** `require_api_key()` now tries the
  existing bearer key first (byte-identical behavior/errors), then an
  Authentik-issued JWT independently — neither is a fallback for the
  other. Before writing this, confirmed from Authentik's own source
  (`authentik/providers/oauth2/models.py`, docstring: *"OAuth2 access
  token, non-opaque using a JWT as identifier"*) that its access tokens
  are genuine signed JWTs verifiable via the provider's JWKS exactly like
  an ID token — not the opaque/introspection-only tokens some OAuth2
  servers issue, so this design is grounded in the real implementation,
  not an assumption. Fetched the live discovery document and JWKS for the
  real `aster-companion` provider first (`issuer`, `jwks_uri`, `RS256`,
  the exact `scopes_supported` list) to hardcode correct, real defaults
  rather than guessed endpoint shapes. Checks both `iss` and `aud`, not
  just signature validity, so a token minted for a different Authentik
  application is rejected. Added `PyJWT[crypto]==2.14.0` as a new
  dependency (none existed before).

  Built a real Python 3.11 virtualenv (this Mac's default `python3` is
  too old for this project's pinned `fastapi`) with every dependency
  actually installed, not just read, and ran the real test suite in it:
  all 48 pre-existing tests still pass unchanged. Added 11 new tests
  against the project's own stated validation criteria: existing bearer
  key unaffected; missing header still 401s; wrong audience, wrong
  issuer, wrong signing key, and expired tokens are each independently
  refused; a malformed bearer value is refused; and a valid Authentik
  token works even with no bearer key configured at all, confirming the
  two credential types are genuinely independent rather than one being a
  silent fallback for the other. Beyond the mocked unit tests, also
  exercised the real live JWKS endpoint over the network (crafted a
  syntactically-valid JWT with a real `kid` from the live endpoint) to
  confirm `PyJWKClient` actually fetches and matches against the real
  deployed Authentik instance, not just a mocked shape.

  **Not yet deployed.** This is committed to git only — LXC 104 doesn't
  have the new dependency installed and `aster-agent.service` hasn't been
  restarted. Deploying means installing `PyJWT[crypto]` on the actual
  host, restarting the service (a brief interruption to the existing
  browser page, which today's few users depend on), and — per M2's own
  definition — a live end-to-end test with a real passkey login through
  the new flow, which needs Jason's own passkey and can't be completed by
  this session. M2 stays open until that happens.
- 2026-09-21 — **Live passkey login proven end-to-end with a real token —
  and a genuinely missing piece of infrastructure found and fixed in the
  process.** No native app exists yet (M3), so a minimal manual test stood
  in for it: temporarily added a second, additive redirect URI to the
  `aster-companion` provider (`https://aster.elliottrook.com/`, Aster's
  own existing page, chosen because Jason's remote session couldn't see
  this session's own browser pane — an in-pane loopback listener
  (`http://127.0.0.1:8765/callback`) was tried first and abandoned for
  exactly that reason) and built a real PKCE authorization URL by hand.
  Jason opened it on his phone and completed a genuine passkey login
  against the new passwordless flow — confirmed live: the screen showed
  only "Sign in to Aster Companion" with a username field, no password
  field anywhere. The first authorization code expired before the manual
  copy-paste round trip finished (Authentik's default
  `access_code_validity` is `minutes=1`); temporarily extended to
  `minutes=5` for this manual test and reverted immediately after.

  The second attempt exchanged cleanly for a real token
  (`POST /application/o/token/` → `200`, real `access_token`/`id_token`/
  `refresh_token`). Decoded (signature ignored only for this inspection)
  to confirm real claims: `iss`/`aud` exactly as configured, `sub` a
  hashed user ID, `email: jason@yampy.ca`, `amr: ["mfa"]`. **Calling
  Aster's real API with this real token first failed with `401`** — not
  a code bug: `aster_agent.py`'s JWKS fetch was failing closed on a
  connectivity error being silently swallowed. Checked directly rather
  than guessing further: `curl` from Aster's own host (LXC 104) to
  Authentik's JWKS endpoint timed out completely (`exit 28`, no response)
  — Lab VLAN 70 had no outbound path to Management VLAN 50 at all, since
  the only rule created earlier in M2 was NPM → Aster, the opposite
  direction. This is a genuine missing requirement of the Authentik-token
  feature itself, not scope creep: verifying a JWT against a JWKS
  requires reaching the JWKS. Added one new narrow OPNsense rule (backed
  up config first): `192.168.70.10` (Aster only, not the whole VLAN) →
  `192.168.50.23:443` (NPM) on interface `opt6` (confirmed Lab VLAN 70's
  real identifier from the interfaces section, not assumed), sequence
  `2680` — positioned before `opt6`'s own `RFC1918_Networks` block
  (sequence `2700`) using the same lesson learned earlier in M2, not
  repeating that mistake. Reloaded; confirmed `curl` from LXC 104 to the
  JWKS endpoint now returns `200`. **This rule is permanent, unlike the
  redirect URI and validity-window changes — Aster genuinely needs it for
  the Authentik-token path to function at all, in production, always.**

  Retried the exact same real token against Aster's real API:
  `GET /v1/models` → `200`, real model list returned. **This is the
  complete, genuine end-to-end proof M2 asked for**: a real passkey
  login, through the real passwordless flow, producing a real token,
  accepted by Aster's real production API through the real NPM/OPNsense
  path. All temporary test-only changes reverted immediately after
  (redirect URIs back to just `aster-companion://callback`,
  `access_code_validity` back to `minutes=1`); the new JWKS egress rule
  was not reverted, since it's required infrastructure, not a test
  artifact. Confirmed via M1's own explicit criteria: **still outstanding
  before M2 can be marked fully closed** — this test proved the LAN path;
  M2's own definition also calls for confirming the same thing over
  Tailscale, not yet separately confirmed.
- 2026-09-21 — **Tailscale path proven; M2 fully closed.** Repeated the
  same real-passkey-login test with Jason's phone off Wi-Fi (cellular,
  Tailscale connected). Re-added the temporary redirect URI and extended
  code validity the same way as the LAN test, reverted immediately after.
  First attempt: Authentik's own login worked correctly (real code, real
  state match), but the browser reported "server can't be found" trying to
  load `aster.elliottrook.com` afterward — a DNS failure, not an auth or
  network failure, confirmed by the wording of the actual error rather
  than assumed. The authorization code was still valid regardless (it
  doesn't depend on the redirect page loading), so the exchange and the
  live API call were both completed anyway: token issued
  (`iss`/`aud`/`sub`/`amr` all correct), `GET /v1/models` against Aster's
  real API returned `200` with the real model list. So the Authentik+Aster
  half of the chain was already fully proven at this point — only the
  phone's own DNS path for this one hostname remained in question.

  Root cause, confirmed by checking documentation rather than
  speculating: `docs/Current-Network-Baseline.md` already records that
  "Tailscale split DNS sends only the `internal` namespace to OPNsense" —
  `elliottrook.com` was never added as a second split-DNS domain, so a
  cellular-only client falls back to public DNS, which has no record for
  it by design. This affects every `*.elliottrook.com` host over
  cellular-only Tailscale, not just Aster — flagged as such rather than
  treated as an Aster-specific fix, and left for Jason to make (Tailscale's
  admin console is a third-party account with no API access from this
  session, and Jason's remote session couldn't see this session's own
  browser pane either, so this genuinely needed his own action).

  Jason added `elliottrook.com` as a split-DNS domain pointed at the same
  nameserver (`192.168.1.1`) the existing `internal` entry already uses.
  First retry still failed identically — isolated by testing
  `git.elliottrook.com` on the same phone/connection, which worked,
  proving the domain-wide DNS fix itself had taken effect and the problem
  was narrower than first thought. Cross-checked directly from this Mac,
  querying OPNsense's real resolver address rather than loopback
  (`dig @192.168.1.1 ...`): both `git` and `aster` resolved correctly to
  `192.168.50.23`, meaning the server-side DNS was already completely
  correct. That left only one explanation: negative DNS caching on the
  phone from before the fix, for the one hostname it had already tried
  and failed on. Confirmed exactly right: after Jason toggled Tailscale
  off and on (forcing a fresh resolver state), `aster.elliottrook.com`
  resolved and returned Aster's genuine `{"status":"ok",...}` health
  response over cellular data.

  **Both halves of M2's validation criteria are now real, verified
  evidence, not assumptions**: a real passkey login producing a real
  token accepted by Aster's real API, proven independently from the LAN
  and from cellular-only Tailscale. Milestone 2 is complete.
- 2026-09-21 — **Milestone 3 started: native macOS app built and running,
  first real chat round trip in progress.** Built `apps/AsterCompanion` as
  a SwiftUI Swift Package Manager app rather than a hand-written
  `.xcodeproj` (a hand-crafted `project.pbxproj` is a real way to end up
  with a silently corrupted, unopenable Xcode project; a package is fully
  buildable via `swift build`/`swift test` and Xcode can open it directly
  for any future work). Ships: `ASWebAuthenticationSession`+PKCE login
  against the live `aster-companion` Authentik application, Keychain
  token storage with silent refresh, a chat UI against Aster's existing
  `/v1/chat/completions`, and idle/thinking `OrbView` states only,
  matching M3's stated scope exactly (no persona picker, no voice, no
  actions). PKCE's cryptography is unit-tested against RFC 7636 Appendix
  B's own reference vector, not just checked for plausible shape.
  `build-app.sh` assembles a real `.app` bundle and registers it with
  Launch Services, since the custom URL scheme needs a genuine bundle to
  route the callback — a raw `swift run` executable can't receive it.

  Jason completed a real interactive login in the running app — the
  first genuinely interactive test of this whole project, since every
  prior verification used a manually-built authorization URL as a
  stand-in for the native app. Two real bugs surfaced and were fixed by
  testing rather than trusting a clean build:
  1. Login appeared to succeed (UI moved to the chat view) but sending a
     message failed with "Not signed in." — the token exchange succeeded
     only in memory. Root cause: `build-app.sh` copied the binary and
     `Info.plist` into the `.app` structure *after* `swift build` had
     already applied its own ad-hoc signature to the loose binary, so the
     assembled bundle's signature didn't cover it (`codesign` showed
     `Info.plist=not bound`) — its identity didn't match what Keychain
     checks reads/writes against, so `SecItemAdd` was failing silently
     every time. Fixed by re-signing the fully assembled bundle as the
     build script's last step, and stopped `KeychainStore.set()` from
     swallowing the result — failures now log the real `OSStatus`.
  2. After that fix, a real message reached Aster's real API (proving
     the entire auth chain end-to-end for the first time from the actual
     app) but got a `502`: `aster-llama.service` on LXC 110 was
     completely inactive — unrelated to anything touched this session, no
     guest on that host had been touched before now. Live-checked rather
     than guessed: the official `scripts/check-aster-b60.sh` passed clean
     (correct `xe` binding, Vulkan sees the real BMG G21 — the documented
     llvmpipe-fallback failure mode was *not* what this was), and a
     directly-timed request once the service had settled came back in
     4.5s, matching the documented baseline exactly — the earlier
     ~14 tok/s reading in the logs was transient cold-start settling, not
     a persistent regression. Jason separately updated drivers around the
     same time. Bumped the app's own client-side timeout from the default
     60s to 120s regardless, since even the documented baseline has real
     headroom above 60s for a heavier grounded query.
  3. A heavier query ("can you run lab doctor") then hit a `504` from NPM
     itself (`openresty`), not from Aster or the app — nginx's default
     60s `proxy_read_timeout` was shorter than the query legitimately
     needed. Fixed with the same safe internal-module approach used for
     the original proxy host (`internalNginx.configure()`, not hand-edited
     config): set `proxy_read_timeout`/`proxy_send_timeout`/
     `proxy_connect_timeout` to `300s` in Aster's own `advanced_config`,
     verified the generated conf and confirmed no regression to any other
     proxied host.

  M3's own "prove the full native-app round trip, local and remote" is
  not yet fully closed — the Tailscale side of the native-app test still
  needs to happen, and a full lab-doctor-weight query hasn't yet
  succeeded end-to-end through the app since the NPM timeout fix.
- 2026-09-21 — **Heavier query succeeded through the app after the NPM
  timeout fix; visual design iterated live with Jason.** Confirmed
  "can you run lab doctor" (the exact query that hit the `504` earlier)
  now completes successfully end-to-end through the real app. M3's LAN
  round trip is proven for real, through the actual native app, not a
  stand-in — the first time this whole project has had a real user
  ask Aster something and get a real answer through the whole chain it
  built.

  Icon and `OrbView` iterated through several real rounds with Jason
  watching the running app, each rebuilt and reverified rather than
  guessed:
  - Wired the accepted icon concept into `Contents/Resources/AppIcon.icns`
    (generated via `sips`+`iconutil`, all standard sizes) and into
    `OrbView` itself as the state-indicator artwork, replacing the
    placeholder circle — the icon was explicitly designed for this dual
    use per the "Visual identity" section.
  - Two real, reported-and-fixed bugs: (1) `Image(_:bundle:)`'s
    named-asset lookup doesn't reliably resolve a loose PNG copied in via
    a plain SPM `resources:` rule — switched to loading it directly via
    `Bundle.module.path(forResource:ofType:)` +
    `NSImage(contentsOfFile:)`, with a loud stderr message instead of
    silent empty space if it ever fails again; (2) the SPM-generated
    resource bundle lives next to the loose executable, not inside any
    app structure — `build-app.sh` now copies it into
    `Contents/Resources/` alongside the icon.
  - Redesigned per direct feedback: circular (`clipShape(Circle())`),
    much larger (420pt), moved from a small header glyph into a faded
    (16% opacity) background layer behind the whole chat view, and
    dropped the original spin-when-thinking rotation.
  - Caught and fixed a real regression of the point of the graphic: an
    always-on continuous pulse (regardless of idle/thinking) was
    calmer but no longer meant anything, since idle and thinking looked
    the same. Idle is genuinely static again; the pulse now starts and
    stops explicitly on the state transition (a fresh short animation on
    the same driving flag interrupts the `repeatForever` loop cleanly),
    so the pulse's presence or absence *is* the thinking signal again.
  - Extended the pulse to also modulate saturation and brightness in sync
    with scale (dim and still at rest, brighter and more colorful at each
    peak), then slowed the whole cycle to 1.6s per Jason's read of it
    live as "perfect" once slowed down.

  Every source and behavioral fix above is tested (existing suite still
  green after each change) and was verified by an actual rebuild +
  relaunch + Jason looking at the running app, not assumed correct from
  reading the code. Nothing here was pushed to origin until confirmed
  working.
- 2026-09-22 — **Native iOS decided against; web client added to scope.**
  Set out to prove M3's Tailscale round trip for the macOS app; the
  request evolved once it became clear the app only runs on this Mac and
  Jason actually wanted phone access, which surfaced a real question this
  project's own Scope section had only partially answered ("designed to
  extend to iOS later... but iOS is not built in this project" — silent on
  *why not*, or what to do instead). Laid out the real mechanics rather
  than assuming: a native iOS install without a paid Apple Developer
  Program membership ($99/year) expires after 7 days and needs Xcode plus
  a physical/wireless USB pairing with a Mac to refresh. Jason has no
  interest in that subscription — a clean, explicit "decided against," not
  a deferral.
  Recommended a browser-based web client instead, not merely as a
  concession: it needs no developer account on any platform, and
  passkey/WebAuthn login isn't a downgrade at all — Mobile Safari's native
  WebAuthn support was already proven working manually against this exact
  Authentik flow during M2's live testing, so the *only* real trade-off is
  weaker token storage (browser storage vs. Keychain), not a worse login
  experience. Jason agreed, and separately confirmed voice (M6) should
  target both the macOS app and the new web client when built, not just
  one — a browser can already do microphone capture and audio playback
  natively, so this is a design-from-the-start decision rather than a
  later retrofit. Scope, Exclusions, M3 and M6 all updated to match. No
  web client code has been written yet.
- 2026-09-22 — **Web client built, deployed, and proven working on both
  LAN and Tailscale — a real milestone, reached through real live
  debugging, not a clean first try.** Added `GET /companion` and
  `GET /companion/orb.png` to `aster_agent.py` (purely additive — `GET /`
  untouched, matching this project's own exclusions), registered a second
  permanent Authentik redirect URI
  (`https://aster.elliottrook.com/companion`, additive alongside the
  native app's `aster-companion://callback`), and implemented PKCE
  entirely with the browser's own Web Crypto API (`crypto.subtle.digest`,
  `crypto.getRandomValues`) — no library dependency. Verified locally
  before ever touching the deployed service: server starts clean, both
  routes return correct content, and the Python f-string's brace-escaping
  (a real risk in a file that already mixes literal JS/CSS braces with
  Python interpolation throughout) was checked by reading back the actual
  rendered output, not assumed correct. Deployed with the same discipline
  as every prior `aster_agent.py` change tonight: pre-deploy backup, full
  59-test suite run on the real host before restarting, restarted clean,
  regression-checked `/` and `/health`.

  First real interactive test (Jason, on Wi-Fi) got the login and orb
  exactly right, but chat replies failed with "Load failed" — diagnosed
  from NPM's own access/error logs rather than guessed: real `499`s
  ("client closed the connection"), meaning iOS Safari itself killed the
  in-flight request, most likely from the tab losing focus during a
  slower query. Fixed by switching to the SSE streaming path
  `aster_agent.py` already supported (`stream: true`), parsing OpenAI-style
  `data: {...}` lines via a manual `response.body.getReader()` loop —
  verified the exact wire format live (both hitting Aster directly and
  through the full NPM/HTTPS path) before trusting the client-side parser
  matched it. A first Tailscale attempt then also failed; retried after
  the streaming fix and **now fully works on both networks** — most
  likely the same root cause (a slow non-streamed reply losing the race
  against iOS backgrounding it) rather than two separate bugs, though
  that's inferred from the fix resolving both, not separately proven.

  **M3's web client sub-item is now complete.** The macOS app's own
  Tailscale round trip is still separately unproven (see that sub-item
  above) — worth Jason's call on whether that still matters now that the
  web client covers "works on my phone" more completely than native iOS
  ever would have, or whether it's fine left as a known gap.
- 2026-09-22 — **Chat bubble transparency and response-length tuning, plus
  a real design conversation about where Aster is headed.** Jason pointed
  out the message bubbles were opaque enough to defeat the point of the
  orb being visible behind them — a real bug on the web client
  specifically, where the "semi-transparent" colors turned out to be
  fully opaque hex values with no alpha channel at all. First fix
  (`.55` alpha web, `.ultraThinMaterial` native) still wasn't transparent
  enough per direct feedback; dropped further (`.18` alpha + stronger
  blur web, a flat `.15`/`.1` tint replacing the material entirely on
  native, since the material's own baseline opacity was working against
  the goal) and verified live on both.

  Separately, Jason reported responses "keep getting cut off." Traced to
  `MAX_RESPONSE_TOKENS` defaulting to 160 — not a bug in tonight's new
  code, a pre-existing shared limit used by every Aster consumer
  including the original browser page. Before just raising a number,
  asked what it should actually be *for* given Jason's real plan: Aster is
  moving toward two new, genuinely different workload shapes — deep
  scheduled analysis (email, news briefings, calendar, photo review) where
  speed doesn't matter, and lightweight Home Assistant integration where
  speed matters and depth doesn't. Neither wants the same ceiling: deep
  analysis wants a far higher budget than fits a synchronous chat window
  (and likely shouldn't run through this same interactive endpoint at all
  — more a scheduled pipeline, like the News Aggregator's own), and HA
  wants shorter replies than today's default, not longer. `get_lab_health`
  already has its own separate, smaller cap
  (`MAX_HEALTH_RESPONSE_TOKENS`) — the right shape here is per-context
  budgets, one per interaction mode, decided when each becomes its own
  scoped project, not one shared number stretched to cover all three.

  Jason confirmed the Companion apps (this chat window) are a genuine
  third category of their own — not the deep-analysis engine, "the
  window that provides responses *to* the analysis," relaying/discussing
  already-digested output from those future scheduled services rather
  than doing deep synthesis itself. Set `ASTER_MAX_RESPONSE_TOKENS=500` in
  `/etc/aster/aster.env` (the officially-supported tuning knob, no code
  change) on that basis specifically — headroom for an occasional
  structured reply, not a target. Verified live: the exact query that cut
  off earlier tonight now completes naturally (`finish_reason: stop`, 342
  of 500 tokens used) instead of truncating mid-sentence. The
  deep-analysis and HA ceilings remain undecided, deliberately — they
  belong to those future projects, not this one.
- 2026-09-22 — Milestone 4 backend + web client, deployed and verified.
  Added a `PERSONAS` registry to `aster_agent.py` ("Sysadmin Aster" = all
  existing tools, unchanged behavior; "Media Automation Aster" = scoped to
  `get_arr_report`, `get_arr_repair_proposal`, `get_current_time`,
  `search_knowledge` only), a per-request `persona` field (default
  `sysadmin`) and an `enabled_tools` field that can only narrow a
  persona's own tool set, never widen it. `select_tools()` and
  `normalized_messages()` now respect both; a new `GET /v1/personas`
  (authenticated) lets both clients discover personas and their allowed
  tools without hardcoding them. The existing hardened system prompt
  (ARR advisory-only, HA read-only, credential refusal, etc.) is
  unchanged and applies to every persona unconditionally — personas only
  narrow tool availability and add a short identity line, they do not
  relax any guardrail. 14 new unit tests added (73 total), all passing
  locally and on the real host's own venv before deploy. Deployed via the
  established discipline: pre-change backup
  (`aster_agent.py.before-m4-352b390` on the host), SHA-256 hash-verified
  transfer, full suite run in an isolated dir on the host's own venv
  before touching the live file, then swap-in and `systemctl restart`.
  Clean restart confirmed via `journalctl` (no errors). Regression-checked
  the untouched legacy `/` page (200), `/companion` (200), and that
  `/v1/personas` and `/v1/models` both correctly 401 without a key.
  Live-tested with a real bearer-key request: `GET /v1/personas`
  authenticated returns both personas with the intended scoped tool
  lists; a `persona:"media"` chat request asking a Home-Assistant
  question got back "This request is out of scope for the Media
  Automation Aster persona. Please switch to Sysadmin Aster..." —
  confirming the scoping holds through the live model, not just in unit
  tests. Web client (`GET /companion`) gained a persona picker
  (switching starts a fresh chat, since persona identity is part of the
  system prompt on every turn) and a per-chat tool checklist scoped to
  the active persona, both wired into `/v1/chat/completions`; rendered
  HTML and the embedded JS were both syntax-checked before deploy.
  **Not yet done:** actual live-UI verification of the web client's new
  picker/checklist (needs a real passkey login, which only Jason's own
  devices can reach — see the browser-tooling limitation noted this same
  session), and the native macOS app has no persona/tool UI yet. Jason
  confirmed both clients should get the same persona/tool UI, so the
  macOS app is next, followed by Jason's own live check of both.
- 2026-09-22 — Milestone 4 macOS app, same day follow-up. Added
  `PersonaModels.swift` (`Persona`/`ToolDescriptor`/`PersonasResponse`,
  decoding the same `GET /v1/personas` shape the web client consumes),
  `AsterClient.fetchPersonas()`, and threaded `persona`/`enabledTools`
  through `AsterClient.send()`. `ContentView` gained a menu-style persona
  picker in the header and a `DisclosureGroup("Tools")` checkbox list
  scoped to the active persona, both persisted per-persona via
  `UserDefaults` (the app's equivalent of the web client's
  `localStorage`, same null-means-unrestricted / all-checked-means-no-key
  semantics). Switching persona clears the in-progress chat, matching the
  web client's same reasoning (persona identity rides in the system
  prompt on every turn). Added `PersonaModelsTests.swift` decoding the
  real backend response shape; full Swift suite (5 tests) passes. `swift
  build` succeeds; the assembled `.app` (via `build-app.sh`) launches and
  stays running without crashing. **Not yet done:** this session has no
  way to drive a native macOS window's UI (no screen-automation tool
  available, unlike the iOS Simulator or the built-in browser), so the
  actual persona-switch/tool-checklist interaction — and both clients'
  live passkey-login round trip generally — still needs Jason's own
  hands-on check before M4 is marked complete.

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
