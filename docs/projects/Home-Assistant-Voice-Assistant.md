# Home Assistant Voice Assistant Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen
> by Jason before implementation begins

## Purpose and desired outcome

Give the household spoken control of Home Assistant-integrated devices —
"turn on the porch light," "set the living room to 70," "turn off the office
lamp" — using local speech-to-text, a local LLM for intent understanding, and
local text-to-speech for spoken confirmation. No cloud speech or cloud LLM
service should see household audio, transcripts or device state.

This is deliberately **not** an extension of the existing read-only Aster
Home Assistant advisor (`docs/projects/completed projects/Aster-Home-Assistant.md`).
That project answers status/health/troubleshooting questions from a sanitized
report and holds no Home Assistant credential or mutation authority. A voice
assistant must actually call Home Assistant services to be useful, which is a
materially higher-privilege capability. This document treats it as new,
separate scope and cross-references the advisor only to avoid duplicating it.

## Current state and evidence

- Home Assistant OS runs as Proxmox VM 103 at `192.168.20.11` on Servers VLAN
  20 (not Trusted, not IoT). Per the Aster Home Assistant advisor's evidence
  log (2026-09-10), the installed versions were Core 2026.9.1 and Supervisor
  2026.09.0, healthy at that time.
- Home Assistant is the only host permitted to initiate access into IoT VLAN
  30 (`docs/Network-Design.md`, `docs/02-IP-Addressing.md`). Known IoT devices
  today: Lutron Caséta bridge (`192.168.30.102`) and Philips Hue bridge
  (`192.168.30.164`), both already integrated with Home Assistant. No lock,
  garage-door or other high-consequence actuator is currently recorded in the
  IP addressing inventory — worth confirming directly in Home Assistant's own
  entity list before finalizing the voice-exposed entity allowlist in
  Milestone 1, since this document's inventory review is documentation-only
  and has not itself queried live Home Assistant state.
- A shared local LLM inference endpoint already exists and is the lab's
  standing local-AI backend: `aster-llama.service` on LXC 110
  (`192.168.70.12:11435`, OpenAI-compatible `/v1`, Qwen3.8 27B `UD-IQ4_XS` on
  an Intel Arc Pro B60 via Vulkan), bearer-authenticated, Lab VLAN 70 only
  (`docs/reference/Aster-Operations.md`). It already serves Aster Agent (LXC 104) and
  the completed MuckScraper news aggregator's summarizer and audio-digest
  narration.
- Local TTS is already vetted on this exact hardware family: the MuckScraper
  Phase 3 audio digest (`docs/projects/completed projects/News-Aggregator-Audio-Digest.md`,
  completed 2026-09-15) installed the prebuilt Piper binary and the
  `en_US-lessac-medium` voice, validated with a real generated sample Jason
  approved (with `length_scale 1.15` after hearing it). That same document
  states the Piper choice "doubles as a trial for a planned Home Assistant
  project" — i.e., this project was already anticipated as Piper's next
  consumer. Reuse that voice/config as the starting point rather than
  re-evaluating TTS voices from scratch, unless Home Assistant's own Assist
  pipeline requires a different packaging of Piper than the standalone binary
  MuckScraper used.
- No local speech-to-text engine, wake-word listener, microphone/speaker
  hardware, or Home Assistant "Assist" pipeline configuration exists yet in
  this repository's record. This is genuinely new build work, not a gap in an
  existing deployment.
- Home Assistant's own Assist framework (wake word, STT, intent/conversation
  agent, TTS, entity exposure allowlist) ships natively with HA Core/
  Supervisor — this project's job is to configure and wire that existing
  framework to local components, not to build a voice pipeline from scratch.
  Whether the installed 2026.9.1 line's conversation-agent options include an
  official integration that can point at an arbitrary OpenAI-compatible `/v1`
  endpoint (matching `aster-llama`'s shape) has not been verified against the
  live instance and is Milestone 1 work, not an assumed fact.

## Scope

- Configure Home Assistant's native Assist pipeline: wake word or
  push-to-talk trigger, local speech-to-text, a local-LLM conversation agent,
  local text-to-speech, and spoken/visual confirmation.
- Point the conversation agent at the existing `aster-llama` endpoint if
  capacity allows, using a dedicated least-privilege bearer key scoped only to
  that `/v1` API (matching the MuckScraper dedicated-key precedent) — not a
  shared key with Aster or MuckScraper.
- Define an explicit, reviewed allowlist of entities exposed to voice control
  (Home Assistant's own per-entity "Expose to Assist" setting), rather than
  blanket area/domain exposure.
- Add a confirmation step for any exposed action Jason and the household agree
  is high-consequence, if any such entity is exposed at all.
- Physical satellite hardware selection (microphone/speaker device — e.g. an
  ESPHome-based satellite or a dedicated voice puck) is in scope to *decide*,
  but its physical installation is a human step outside any authorization
  stream's autonomy (see the standard's "does not extend to anything a
  physical human step is required for").

## Out of scope

- Any change to the existing read-only Aster Home Assistant advisor's
  curriculum, report or authority boundary.
- General home-automation rewrites, new automations unrelated to voice
  control, or new IoT devices.
- Camera/Frigate voice integration — that is Surveillance Expansion's own
  Milestone 4 and is not duplicated here.
- Cloud speech-to-text, cloud text-to-speech, or any cloud conversation agent
  (Google/Amazon/OpenAI-hosted). Violates the lab's local-first/privacy
  principle and is not proposed as an option.
- Granting Aster (LXC 104) any Home Assistant credential, service-call
  ability, or entity-state access. The voice pipeline runs inside Home
  Assistant's own process using Home Assistant's own existing authority over
  its already-integrated devices; it does not create a new credentialed path
  from Aster into Home Assistant.
- Multi-room/whole-house satellite rollout in the first pass — start with one
  bounded pilot location.

## Authority model

- **Home Assistant** remains the sole authority for IoT VLAN 30 entity state
  and service calls. This project does not change that; it adds a new *input
  path* (voice, via Assist) into authority Home Assistant already has.
- **`aster-llama`** remains a shared inference utility, not a decision-maker
  with direct device access — it only returns text (parsed intent/response);
  Home Assistant's own Assist/intent framework is what actually executes a
  service call, gated by the entity exposure allowlist.
- **This project document** owns the voice-specific design, risk acceptance
  and milestone evidence. `docs/reference/Aster-Operations.md` and Home Assistant's own
  configuration remain authoritative for the respective services' live state.

## Architecture and data flows (proposed)

```
[Wake word / push-to-talk on satellite device, VLAN TBD]
        |  audio
        v
[Home Assistant Assist pipeline, VM 103, Servers VLAN 20]
        |  local STT (e.g. faster-whisper add-on, runs on/near VM 103)
        v
[Text] --bearer-authed HTTPS--> [aster-llama /v1, LXC 110, VLAN 70]
        |  text response / structured intent
        v
[Home Assistant conversation agent resolves intent against
 the reviewed "Expose to Assist" entity allowlist]
        |  service call (existing HA authority, IoT VLAN 30 devices)
        v
[Local TTS (Piper) speaks confirmation back through the satellite device]
```

Open architecture questions to resolve in Milestone 1, not assumed here:

- Does Home Assistant 2026.9.1's conversation-agent integration options
  support an arbitrary OpenAI-compatible `/v1` endpoint, or does reaching
  `aster-llama` require a community/custom integration? This changes the
  trust and update-maintenance picture and must be checked against the live
  instance rather than assumed from the model's general knowledge.
- Does local STT (Whisper via a HA add-on/container) run acceptably on VM
  103's existing allocation, or does it need its own resource increase or a
  separate small VLAN-70 LXC? VM 103 currently holds 4 GB per the Surveillance
  Expansion capacity note (2026-08-30); STT model loading has its own memory
  footprint that has not been measured against that allocation.
- Does `aster-llama` have concurrent-request headroom to add voice-intent
  parsing as a third consumer alongside Aster chat and MuckScraper's
  summarizer/digest, or will voice command latency compete with those under
  load? Not measured — flag as an open capacity question rather than assuming
  the single-GPU/single-model backend scales for free (see Pre-start risk
  assessment).
- What physical VLAN does the satellite microphone/speaker device sit on?
  A voice satellite is itself a new physical IoT-class device; per network
  design it likely belongs on IoT VLAN 30 or Trusted, not directly on Lab
  VLAN 70 — needs an explicit decision, not a default.

## Privacy and security design

- All speech-to-text and text-to-speech processing stays local; no cloud
  speech or cloud LLM service is contacted, matching the lab's "maximum
  practical privacy" principle and the precedent set by the local-Piper
  decision in the audio digest project.
- Microphone audio is processed transiently for wake-word/command capture and
  is not retained beyond what Home Assistant's own Assist pipeline needs to
  operate, unless Jason explicitly enables debug recording for troubleshooting
  — and if so, that recording must be time-bounded and excluded from any
  backup or Aster-visible path.
- The conversation agent's connection to `aster-llama` uses its own
  dedicated, least-privilege bearer key, scoped only to that `/v1` API, so a
  compromise of the Home Assistant integration cannot reach Aster's chat
  history, MuckScraper's key, or any other consumer's credential.
- Home Assistant's voice authority is bounded by the "Expose to Assist"
  allowlist, reviewed and approved by Jason before Milestone 4 activates any
  entity. Nothing is exposed by default just because it exists in Home
  Assistant.
- No new inbound path is created. The satellite device only needs to reach
  Home Assistant's existing Assist pipeline endpoint on its own VLAN; no new
  firewall rule opens Lab VLAN 70 or Servers VLAN 20 to a broader source than
  today.
- This project does not add any capability to the existing Aster Home
  Assistant advisor and does not weaken its no-credential, no-mutation
  boundary.

## Pre-start risk assessment

**Objective/scope/stream:** as defined above; stream not yet chosen.

**Affected systems:** Home Assistant VM 103 (Servers VLAN 20), IoT VLAN 30
devices currently integrated with Home Assistant (Lutron Caséta, Philips Hue),
`aster-llama` LXC 110 (Lab VLAN 70), a new physical satellite device (VLAN
TBD), and household members whose voice/audio is processed.

**Current versions/dependencies:** Home Assistant Core 2026.9.1 / Supervisor
2026.09.0 as last confirmed 2026-09-10 (re-verify before implementation, since
this document does no live discovery); `aster-llama.service` current
production model/version per `docs/reference/Aster-Operations.md`.

**Confidentiality/secret-handling risks:** a new bearer key must be minted for
the conversation agent's `aster-llama` access and stored the same way existing
Aster/MuckScraper keys are stored (root-owned, group-readable env file, never
in Git). Voice transcripts could contain incidental household conversation if
wake-word detection false-triggers — bounding retention (above) mitigates this.

**Availability/integrity/privacy/recovery risks:**
- A misrecognized voice command could trigger an unintended device action.
  Today's known exposed-candidate devices are lighting (Hue, Caséta) — no
  lock or safety-critical actuator is recorded in current inventory, so the
  worst-case blast radius appears bounded to lighting/shade state, but this
  must be *confirmed* against Home Assistant's live entity list before
  Milestone 4, not assumed from this document's static inventory review.
- Adding a third concurrent consumer to the shared `aster-llama` backend
  (after Aster and MuckScraper) could degrade response latency for all three
  under simultaneous load. Not measured. **Open decision requiring Jason's
  input:** accept shared-capacity risk and measure in Milestone 1, or scope a
  separate/smaller local model for voice-intent parsing specifically because
  voice interactions need lower latency than Aster's deliberate
  21–53-second-class advisory answers tolerate.
- Home Assistant's Assist pipeline is a new attack surface on VM 103 if a
  community/custom conversation-agent integration is required to reach
  `aster-llama` — untrusted third-party code review is needed before
  installation, consistent with the "downloading/executing files from
  untrusted sources" caution.

**Irreversible/destructive operations:** none anticipated. All proposed
changes (Assist configuration, entity exposure list, new bearer key, add-on
installation) are reversible by disabling the pipeline/add-on and revoking the
key; existing dashboard/automation control of Home Assistant is unaffected
either way, since this augments control paths rather than replacing them.

**Expected authentication/firewall/DNS/storage/external-service changes:** one
new bearer key (Home Assistant → `aster-llama`); no new inbound firewall rule
expected beyond the satellite device reaching Home Assistant's existing
pipeline endpoint on its own VLAN — exact rule, if any, to be confirmed once
the satellite's VLAN placement is decided.

**Recovery checkpoint/rollback/abort:** snapshot Home Assistant VM 103 before
enabling Assist/local-LLM configuration; rollback is restoring that snapshot
or simply disabling the Assist pipeline and conversation-agent integration,
which returns Home Assistant to its current dashboard/automation-only control
model with no residual state.

**Test strategy:** functional voice-command tests in a single pilot area
before any wider rollout; synthetic/played-back audio for adversarial testing
(attempting to trigger unintended actions via ambiguous or injected phrases)
rather than relying only on live household speech.

**Likely service interruption:** none to existing Home Assistant dashboard/
automation function; Assist pipeline failure should fail closed (voice command
ignored, existing control paths unaffected) rather than failing open.

**Backup/Doctor/monitoring/NetBox/wiki impacts:** see the integration
checklist below.

**Unresolved decisions requiring Jason's acceptance before work starts:**

1. Does this reuse `aster-llama`, or does voice-intent latency justify a
   separate smaller local model/instance? (Capacity not yet measured.)
2. What physical satellite hardware and which VLAN does it sit on?
3. What is the final entity exposure allowlist, confirmed against live Home
   Assistant state (not just this document's static device inventory)?
4. Does any exposed entity warrant a spoken confirmation step before
   executing, and what phrase/UX pattern?
5. Is a community/custom Home Assistant integration required to reach an
   OpenAI-compatible endpoint, and if so, who reviews its code before
   installation?
6. Audio retention policy for debugging: allowed at all, and if so, for how
   long and stored where?

## Persistence plan

This document is the durable checkpoint. No implementation state exists yet.
On resume: re-read this document and the current live Home Assistant/
`aster-llama` state, confirm no unresolved decision above has silently been
assumed, and continue from the last checked milestone box.

## Milestones

- [ ] **M1 — Discovery and requirements.** Confirm live Home Assistant
  version and Assist/conversation-agent integration options; confirm live
  entity inventory and draft the voice-exposure allowlist; measure
  `aster-llama` concurrent-capacity headroom; decide satellite hardware and
  VLAN placement; resolve the open decisions above with Jason.
- [ ] **M2 — Architecture and risk acceptance.** Finalize the design above
  against M1's findings; present the pre-start risk assessment; Jason accepts
  it and selects Stream M or Stream A.
- [ ] **M3 — Local STT/TTS pipeline.** Deploy local speech-to-text (e.g. a
  Whisper add-on) and reuse/extend the vetted Piper TTS configuration inside
  Home Assistant's Assist pipeline; validate voice round-trip with no device
  action wired yet.
- [ ] **M4 — Conversation agent and entity allowlist.** Wire the local-LLM
  conversation agent to `aster-llama` (or the decided alternative) with its
  own dedicated bearer key; apply the reviewed entity exposure allowlist;
  add confirmation steps for any entity that needs one.
- [ ] **M5 — Validation.** Functional command tests, false-wake/misrecognition
  behavior, adversarial phrase tests, concurrent-load latency test against
  Aster and MuckScraper, restart/reboot resilience, rollback test.
- [ ] **M6 — Observability, backup, documentation and graduation.** Close the
  integration checklist below, record final architecture and accepted
  limitations, and move this document to `completed projects/` only once the
  graduation criteria pass.

## Validation and evaluation

- Functional: representative household commands succeed against the exact
  exposed entity set, no more and no less.
- Least-privilege/denied-action: commands targeting non-exposed entities are
  correctly refused/ignored.
- Adversarial: ambiguous, malformed and injected phrases (including phrases
  played back through the TTS output itself, to check for a feedback loop) do
  not trigger unintended actions.
- Restart/reboot: Home Assistant, the satellite device and `aster-llama`
  restart independently without leaving the pipeline in a broken or
  fail-open state.
- Regression: existing Aster Home Assistant advisor answers and existing
  Aster/ARR/MuckScraper `aster-llama` consumers are re-tested for latency and
  correctness after this project adds a third concurrent workload.
- Rollback: disabling the Assist pipeline/integration leaves Home Assistant's
  existing dashboard and automation control fully functional with no residual
  credential or state.

## Observability and maintenance

- Add a Home Assistant Doctor check (new `check_*` function in
  `scripts/doctor.sh`, following the existing `check_home_assistant_backup_truenas`
  pattern) covering Assist pipeline/add-on health and the new bearer key's
  validity, without adding a new UPS/state class the existing `check_aster`
  family doesn't already model.
- No secret-bearing output in any check; only health/availability signals.

## Backup, restore and rollback

- Home Assistant VM 103's existing backup coverage (per
  `docs/05-Backups.md`) extends naturally to the new Assist/add-on
  configuration once it lives inside the VM; confirm during M6 that the
  existing backup job actually captures the new add-on's configuration
  directory rather than assuming it does.
- The new `aster-llama` bearer key is recorded only by storage location and
  recovery method, never its value, matching existing key-handling practice.
- Rollback path: restore the pre-Assist VM 103 snapshot, or disable the
  Assist pipeline/integration and revoke the dedicated bearer key.

## Documentation and systems-of-record updates (required integration checklist)

- [ ] **HomeLab Doctor** — add an Assist-pipeline/bearer-key health check;
  not applicable to add anything to the existing Aster Home Assistant advisor
  checks, which stay unchanged.
- [ ] **Monitoring/alerting** — decide whether Assist pipeline failures need a
  Beszel/Prometheus signal beyond Doctor, or whether Doctor alone is
  sufficient given the household will notice a non-functioning voice command
  immediately (low silent-failure risk relative to, say, a backup job).
- [ ] **Backup and recovery** — confirm VM 103's existing backup captures the
  new add-on/integration configuration (see above); no new database or
  credential store beyond the one new bearer key.
- [ ] **NetBox** — record the satellite device (model, VLAN, IP/DHCP
  reservation) once hardware is chosen; not applicable until then.
- [ ] **Human wiki** — add operator guidance: what commands work, what's
  intentionally not exposed, how to disable the pipeline.
- [ ] **Aster mirror/snapshot** — not applicable. This project adds no new
  Aster capability or credential; the existing Aster Home Assistant advisor
  entry is unaffected and should not be edited to imply otherwise.
- [ ] **Operational reference and runbooks** — extend `docs/reference/Aster-Operations.md`
  or a Home Assistant–specific operations page with the Assist pipeline setup,
  the dedicated key's storage location, and the disable/rollback procedure.
- [ ] **Repository documentation** — update `docs/01-Architecture.md` and
  `docs/02-IP-Addressing.md` once the satellite device and any new VLAN path
  are decided; update this project's own status in
  `docs/projects/README.md` (left to whoever wires the portfolio table per
  this task's instructions).
- [ ] **Diagrams/rack records** — add the satellite device once physically
  placed; not applicable before then.
- [ ] **Homepage/service discovery** — not applicable in the usual sense (no
  new web UI); consider a simple Homepage status card for "voice assistant
  online" if useful, no credentials embedded.
- [ ] **Authentication/authorization** — the new bearer key is the only new
  identity; no Authentik/SSO involvement, since this is a device-to-device
  API key, not a browser login.
- [ ] **DNS, certificates and firewall** — assess once satellite VLAN
  placement is decided; expect at most a narrow rule for the satellite device
  to reach Home Assistant's existing pipeline port, not a new broad path.
- [ ] **Automation and schedules** — not applicable; this is an interactive
  voice feature, not a scheduled job.
- [ ] **Security inventory** — record the new bearer key's existence, storage
  location and rotation owner; no plaintext secret in Git.

## Graduation criteria

All milestones complete with recorded evidence; the entity exposure allowlist
matches what Jason approved; adversarial and regression suites pass on the
production `aster-llama` (or decided alternative) path; Home Assistant's
existing advisor, dashboard and automation function are unaffected; backup and
rollback are proven; the integration checklist above is closed or marked not
applicable with reason.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## Close-out

Not applicable yet — this project has not started.

## References

- `docs/Project-Creation-Standard.md` — lab ethos, authorization streams, risk
  assessment and template requirements this document follows.
- `docs/projects/completed projects/Aster-Home-Assistant.md` — the existing
  read-only advisor this project deliberately does not duplicate or modify.
- `docs/projects/completed projects/News-Aggregator-Audio-Digest.md` — local
  Piper TTS precedent explicitly noted there as a trial for this project.
- `docs/reference/Aster-Operations.md` — `aster-llama.service` endpoint, key handling
  and service operations reference.
- `docs/02-IP-Addressing.md`, `docs/Network-Design.md` — current VLAN and
  device inventory used for the architecture and risk sections above.
- `docs/projects/Surveillance-Expansion.md` — Milestone 4 (Home Assistant
  integration for cameras), cross-referenced but not duplicated.
