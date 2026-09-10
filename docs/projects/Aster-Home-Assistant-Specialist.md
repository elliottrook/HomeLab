# Aster Home Assistant Specialist

> Status: Active — Milestone 0 substantially complete; Milestone 1/2 groundwork
> built and locally tested; live deployment pending a session with lab
> network access
>
> Project owner: Jason
>
> Started: 2026-09-10

## Purpose

Make Aster a trustworthy advisor for the household's Home Assistant
deployment: the Philips Hue, Lutron Caséta and Aqara M3 (Matter)
integrations, the HomeKit Bridge presentation layer, and household
automations. Aster must answer operational questions, explain how an
automation is supposed to behave, and diagnose bounded evidence without
exposing the Home Assistant long-lived access token or controlling a
device by default.

This is Aster's second specialist domain after the ARR stack (media
automation), following the exact milestone ladder and testing rigor
[`Aster-Arr-Stack-Manager.md`](Aster-Arr-Stack-Manager.md) proved out:
**0** scope/inventory → **1** advisory knowledge only → **2** bounded
read-only live evidence → **3** action-proposal rehearsal → **4** a
graduated, purpose-built broker for exactly one repair operation. No
credential ever touches Aster or Hermes directly at any stage.

## Authorization

**Per-project authorization granted 2026-09-10** (see `CLAUDE.md`,
"Per-project authorization" section), extended informally in the same
conversation with additional risk framing: Jason designated Aster and
Home Assistant as low-risk testing grounds specifically because neither
is a hard production dependency — Home Assistant is a pilot deployment
with its own recovery point (`Fresh HAOS installation`) and native/VM-level
backups, and Aster's own recovery coverage graduated under its own
project. Both can be stopped and restarted freely without breaking any
other system. Claude may execute this project's state-changing steps —
Hermes skill authoring, Aster agent code changes, report producer/broker
code, test-fixture design, and (once a session has live lab access)
deployment — without asking before each individual step, through Aster's
graduation gate for this specialty. This does not waive, for any action
taken under it:

- a rollback route documented before the action, not after;
- the least invasive change that meets the step's objective, preserving
  the lab's existing security/privacy posture everywhere else;
- stopping and asking about anything genuinely unanticipated, especially
  a real safety/privacy trade-off;
- or a physical human step, which no authorization can substitute for.

Real data is preferred throughout (this repo's existing Home Assistant
documentation in `docs/04-Operations.md` and `PROJECTS.md` Phase 7 is the
knowledge source). Synthetic/fixture data is permitted, and used
extensively in this document's own evidence log, specifically for local
test cases where a live claim is not being made — never as a stand-in for
an actual operational result.

Every state-changing step taken under this authorization is logged in the
Evidence log at the bottom of this document as it happens, matching this
repository's standard project-tracking convention.

### Session continuity

This project was started from a cloud Claude Code Remote session with no
network path to the lab (confirmed: no route to `192.168.20.11` Home
Assistant or `192.168.70.10` Aster LXC 104 — see Milestone 2 below). All
work that only needs local file/code access (design, code, tests, docs)
proceeds from such a session; anything needing live SSH/API access to lab
hosts is explicitly flagged as pending a session with real connectivity,
the same handoff pattern already used for the NUT UPS load check and the
UniFi PoE switch removal earlier in this repository's history. A Routine
(`trig_01Tq9kn6TWXt9TKse9LJMUws`, every 4 hours) wakes this same session to
resume the next unchecked milestone item if a run ends early from a
context/token limit, so the project keeps moving without Jason having to
manually restart it.

## Authority and safety boundary

| Concern | Authority / rule |
|---|---|
| Current deployment facts | Reviewed operational reference (`docs/04-Operations.md`, `PROJECTS.md` Phase 7) and bounded live evidence |
| Decisions, experiments and acceptance evidence | This repository's project records |
| Home Assistant long-lived access token | Private storage only; never Git, model context, Hermes skills or chat output |
| Read-only health | Sanitized, schema-validated, aggregate-only report produced outside Aster |
| Home Assistant mutations | Not permitted in this project phase; every future action is separately specified and approved |

The manager must not infer that a Home Assistant token is read-only merely
because it is dedicated. A Home Assistant long-lived access token is a
full-account credential by default — it can control every entity. Before
any live integration, a purpose-built least-privilege report producer
sits between Aster and Home Assistant (see Milestone 2); the token never
reaches Aster or Hermes.

No proposed action may unlock a lock, disarm or bypass a safety sensor,
change a climate setpoint, run a scene or script, trigger or disable an
automation, or reconfigure an integration. It may explain the impact,
provide a reviewable command or UI path, and name the exact approval
required. Aqara's six water sensors, shutoff valve and lock remain
especially sensitive: Aqara itself owns their safety behavior even though
they are visible through Matter, and no proposal may treat them as
routine.

## Initial knowledge scope

The initial curriculum covers:

- Home Assistant OS 18.2 on Proxmox VM 103 (`192.168.20.11`, Servers
  VLAN 20), its role as the sole automation authority, and the
  minimum-access firewall rule that lets it alone reach IoT VLAN 30;
- the Philips Hue, Lutron Caséta and Aqara M3 (Matter) integrations and
  their reserved addresses;
- the HomeKit Bridge presentation boundary: which domains it publishes
  (`light`, `switch`, `lock`, `climate`, `cover`, `fan`, `vacuum`, `scene`,
  `script`, `binary_sensor`) and which it deliberately excludes (media
  players, cameras, general sensors, automations, buttons, helpers);
- the validated Laundry automation pattern (Hue Hall motion → `Laundry
  motion lighting` script → `Laundry bright` scene + `Laundry occupancy
  timer` helper → a separate `timer.finished` automation) as the
  reusable trigger/condition/action/scene/script/helper/trace pattern for
  every later automation;
- HACS is installed and authenticated without an elective community
  repository added; installation alone is not approval to expand scope;
- Aqara's safety-ownership boundary: six water sensors, the shutoff valve
  and the lock are visible through Matter, but Aqara retains their safety
  behavior;
- drift handling: stale integration addresses, HomeKit pairing loss, and
  "unknown" instead of a guessed current entity state; and
- refusal boundaries for the long-lived access token, unlock/disarm
  requests, climate/scene/script/automation mutation, and any request
  that would reveal room-level occupancy or an individual's presence.

Teaching material must be concise, source-linked and free of live URLs
that would expand access, secret-bearing examples, or household presence
detail. A later operational reference page must be reviewed before it
enters Aster's curated snapshot, matching the ARR project's own
Milestone 0 requirement.

## Milestone 0 — Scope and inventory

- [x] Inventory Home Assistant's version, role, network boundary,
  integrations and documented health through existing reviewed evidence.
  Done from `docs/04-Operations.md` ("Home Assistant pilot") and
  `PROJECTS.md` Phase 7 — no live access was needed for this pass. Live
  entity/automation counts still require a session with lab network
  access; see Milestone 2.
- [x] Identify the smallest useful sanitized health schema; it must
  contain no token, entity_id, friendly name, room/area, or automation
  name. Defined as a per-domain aggregate schema (status, coverage,
  entity_total/on/off/unavailable/unknown) covering the 9 HomeKit-published
  domains that have a defensible on/off state mapping, plus `automation`
  reused for enabled/disabled counts — `scene` is deliberately excluded
  because its HA `state` is a last-activation timestamp, not an on/off
  signal, so it has no honest mapping onto this schema (see
  `services/aster-agent/home_assistant_report.py`).
- [ ] Write a reviewed operational reference page with provenance, review
  date, known exclusions and an explicit distinction between current
  facts and historical cleanup notes. `docs/04-Operations.md`'s existing
  "Home Assistant pilot" section is a strong source but has not yet been
  given the authority/review-date metadata the Sysadmin Second-Brain's
  ingestion pipeline expects, nor added to the Aster knowledge manifest.
- [ ] Record every existing automation that can change a device state so
  the manager never duplicates it blindly. Only the Laundry pattern is
  documented in this level of detail today; a full automation inventory
  needs live Home Assistant access.

Completion gate: the review names every source, excluded field and
dependency; two independent reviewers can locate no credential or private
household-presence content.

## Milestone 1 — Advisory Hermes skill and Aster knowledge

- [x] Create a versioned Hermes Home Assistant manager skill that is
  advisory-only.
  [`services/hermes-skills/home-assistant-manager/SKILL.md`](../../services/hermes-skills/home-assistant-manager/SKILL.md),
  structurally tested by
  [`test_home_assistant_manager_skill.py`](../../services/hermes-skills/test_home_assistant_manager_skill.py)
  (1/1 passing), mirroring the ARR skill's frontmatter/safety-boundary
  test pattern exactly.
- [ ] Install the reviewed skill into Hermes' user-local skill directory
  and verify a fresh Hermes session recognizes it. Needs a session with
  access to LXC 104.
- [ ] Add reviewed Home Assistant operational material to the Aster
  snapshot manifest. Source material is ready (see Milestone 0's
  unchecked reference-page item); the manifest edit and deterministic
  snapshot rebuild need live LXC 104 access.
- [x] Wire a read-only `get_home_assistant_report` tool into the Aster
  agent itself, with an advisory system-prompt safety boundary mirroring
  the existing ARR paragraph (no device control, no claimed action, no
  token/room/presence disclosure, aggregate-only report data). Added to
  [`services/aster-agent/aster_agent.py`](../../services/aster-agent/aster_agent.py)
  (tool definition, intent-detection regex, dispatch, preload wiring, and
  the system-prompt paragraph). The full existing `services/aster-agent`
  test suite plus new tests passed **51/51** locally with zero
  regressions before this was considered done.
- [ ] Run source-aware question tests against the deployed Aster
  snapshot. Needs live LXC 104 access; targeted local unit tests already
  cover tool-selection and dispatch behavior (see Evidence log).
- [ ] Run adversarial tests (token requests, destructive automation
  cleanup, prompt injection embedded in Home Assistant notes) against the
  deployed instance. Needs live LXC 104 access.

Completion gate: Aster answers the accepted questions with provenance,
refuses unsafe or secret-bearing requests, and does not claim live state
without the sanitized report.

## Milestone 2 — Bounded read-only live evidence

- [x] Define the strict v1 sanitized Home Assistant report contract and a
  local validator with freshness, field allow-list, aggregate-only and
  cross-field-consistency tests.
  [`services/aster-agent/home_assistant_report.py`](../../services/aster-agent/home_assistant_report.py)
  mirrors `arr_report.py`'s rigor (regular-file/permission/size checks,
  freshness window, strict schema, aggregate-only values) plus one
  addition specific to this domain: a `entity_total ==
  on+off+unavailable+unknown` consistency check, since a producer bug
  here would misrepresent household device state rather than just a
  queue count.
  [`test_home_assistant_report.py`](../../services/aster-agent/test_home_assistant_report.py):
  **14/14 passing.**
- [x] Build a root/operator-owned report producer outside Aster that
  reads Home Assistant's REST API with a private long-lived token.
  [`scripts/produce-aster-homeassistant-report.py`](../../scripts/produce-aster-homeassistant-report.py)
  reads the token from a mode-600-enforced private file (never a CLI
  argument or a process-list-visible env value), calls `GET /api/states`,
  aggregates per-domain counts using a documented, revisable state
  classification table (see the script's own comments — the per-domain
  on/off state-string mapping is a first-pass judgment call, explicitly
  flagged for validation once real HA data is available), and writes the
  report atomically at mode 640.
  [`test_produce_aster_homeassistant_report.py`](../../scripts/test_produce_aster_homeassistant_report.py):
  **13/13 passing** against synthetic fixture data, including one test
  that feeds the producer's own output through the real contract
  validator, and one that asserts no entity_id ever appears in the
  written report.
- [x] Add a CLI validator matching the ARR project's pattern.
  [`scripts/validate-aster-homeassistant-report.py`](../../scripts/validate-aster-homeassistant-report.py),
  smoke-tested manually against a fixture report.
- [ ] Deploy the producer to a privileged host with a real,
  least-privilege Home Assistant long-lived access token, and validate
  the report schema/freshness against live Home Assistant state. Blocked
  on live lab network access — confirmed unreachable from this session
  (`192.168.20.11:8123` and `192.168.70.10:80` both timed out).
- [ ] Give Aster read-only access to only that report directory
  (systemd-level permission, mirroring the ARR/health report pattern).
  Needs live LXC 104 access.
- [ ] Test stale, malformed, partial and unavailable reports against the
  deployed agent; the manager must report uncertainty rather than retry
  arbitrary network targets. Partially covered locally (a
  malformed/oversized/stale/rejected-field report is refused by
  `execute_tool`'s dispatch in a local test); full live-agent test
  pending deployment.

Completion gate: Aster can diagnose the bounded implemented report state
(per-domain aggregate counts) without holding a Home Assistant credential
or making an arbitrary HTTP request.

## Milestone 3 — Action-proposal rehearsal

Not started. Design note for when this milestone opens: unlike an ARR
mutation (which can touch an irreplaceable download or a monitored-item
setting), a Home Assistant entity state is normally trivially reversible
— a toggled light, an acknowledged automation, a re-run scene can be
undone with the same mechanism that changed it. That lowers the *cost of
a mistake* relative to ARR, but it does not lower the bar for how this
milestone is built: the same dry-run-first, single-use task-specific
approval, precondition-checked, fully-audited broker pattern from the ARR
project still applies, and the water/shutoff/lock exclusion in the safety
boundary above is absolute regardless of reversibility. If a synthetic
Home Assistant automation or helper entity is useful for rehearsing the
broker against something disposable (mirroring the ARR broker's
loopback/fixture Radarr rehearsal), create one deliberately for that
purpose rather than testing destructively against a real household
automation.

- [ ] Define each candidate action as a separate project decision with
  target, identity, validation, audit output, timeout, rollback and
  exact approval moment.
- [ ] Start with dry-run/proposal output only.
- [ ] Compare the proposal against a manually reviewed operation before
  any real mutation is enabled.
- [ ] Treat every mutation as a separate graduation gate. No standing
  approval or natural-language request grants general Home Assistant
  control.

Completion gate: no action capability exists unless its individual
evidence and approval design pass review.

## Milestone 4 — Graduated Home Assistant read and repair capability

Not started. This milestone is the only path from advisory answers to
Aster being able to read current Home Assistant state and repair a
defined problem. It does **not** grant a general Home Assistant
administrator, the raw long-lived access token, broad shell access, or
standing permission to make changes.

- [ ] Define a dedicated Home Assistant broker with one narrow,
  authenticated operation per endpoint. The broker, not Aster or Hermes,
  holds the long-lived access token and rejects every undeclared route,
  method, field and target.
- [ ] Select the initial repair action separately, following the same
  candidate-record shape the ARR broker uses (`broker.py`,
  `issue_candidate.py`, `proposal.py`, `state.py`).
- [ ] Start in a disposable or no-op mode against a synthetic/test entity
  or automation created for this purpose.
- [ ] Add a current, sanitized report for reading Home Assistant health
  and aggregate domain state. Aster must distinguish report state, age
  and coverage from a successful repair action.
- [ ] Enable no more than one low-blast-radius repair action at a time.

### Graduation test gate

Before any action is called a graduated Aster Home Assistant capability,
all of the following must pass repeatedly against the production-shaped
broker and a disposable target where mutation is required:

| Test | Required result |
|---|---|
| Read boundary | Aster answers only from a fresh validated report; expired, malformed or partial reports produce a clear unknown/limited result |
| Authorization | Missing, stale, replayed, cross-domain or out-of-scope requests are denied by the broker without reaching Home Assistant |
| Approval | A natural-language request alone cannot mutate; the broker accepts only the recorded, task-specific approval token/context |
| Schema and target | Unknown fields, arbitrary entity_ids, path traversal, bulk selectors and injected instructions are rejected |
| Safety | A dry run states exact scope, preconditions, validation and rollback before a real action is possible |
| Repair behavior | The one approved action succeeds on a disposable/synthetic target, is idempotent or safely reports prior completion, and cannot widen to a water/shutoff/lock entity or an automation-logic change |
| Failure behavior | Timeout, Home Assistant error, stale report and postcondition failure stop safely, retain the prior state, and emit a bounded audit record without secrets or household details |
| Regression | Knowledge, credential-refusal, prompt-injection, destructive-request and original Aster graduation suites continue to pass after every broker or model change |

### Completion gate

Aster graduates to **bounded Home Assistant read and repair** only when
the reviewed sanitized-report path and a single purpose-built repair
operation satisfy every graduation test above in repeated runs, with
recorded source provenance, least-privilege broker evidence, audit
output and a tested rollback or non-reversibility decision. Jason must
retain the explicit, action-specific approval moment. Passing this gate
authorizes only the enumerated repair operation; it does not authorize
general Home Assistant control or future actions.

## Test matrix

| Class | Required proof |
|---|---|
| Knowledge | Correct integration/automation-pattern answer with cited source and review date |
| Drift | Reports stale integration address or conflicting sources without silently choosing one |
| Uncertainty | Says what evidence is missing instead of fabricating device or automation state |
| Privacy | Refuses the long-lived token, room/area detail, and any individual-presence question |
| Safety | Refuses unapproved unlock, disarm, setpoint, scene/script run, or automation change |
| Report boundary | Rejects malformed/expired reports and never reaches Home Assistant directly |
| Regression | Repeats the accepted suite after model, snapshot, Hermes or Home Assistant updates |

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-10 | 0 | Reviewed `docs/04-Operations.md` "Home Assistant pilot" and `PROJECTS.md` Phase 7 as the real-data knowledge source; confirmed `scripts/doctor.sh`'s existing `check_home_assistant_backup_truenas` and `configs/devices.conf`'s `home-assistant` entry. No fabricated facts used. | Scope/inventory pass complete from repo-available evidence; live entity/automation counts remain open |
| 2026-09-10 | Baseline | Established a clean local test baseline before changing production-adjacent code: installed `httpx`, `fastapi`, `pydantic` locally and ran the full existing `services/aster-agent` suite — 32/32 passed with zero prior modifications. | Safe to extend `aster_agent.py` with confidence any regression would be caught |
| 2026-09-10 | 0/2 | Designed the v1 sanitized report contract in `home_assistant_report.py`: 10 domains (9 HomeKit-published domains with a defensible on/off mapping, plus `automation`), `scene` deliberately excluded with reasoning recorded in-code. Ran its dedicated test suite. | **14/14 local tests passed** |
| 2026-09-10 | 1 | Wrote `services/hermes-skills/home-assistant-manager/SKILL.md`, grounded only in already-documented real facts (Hue/Lutron/Aqara, HomeKit domain publish/exclude list, the Laundry automation pattern, HACS scope discipline, Aqara safety ownership). Wrote its structural test mirroring the ARR skill's test exactly. | **1/1 local test passed** |
| 2026-09-10 | 1/2 | Wired `get_home_assistant_report` into `aster_agent.py`: tool definition, intent regex, dispatch, preload-without-round-trip, and an advisory system-prompt paragraph mirroring the ARR paragraph's structure (no control, no claimed action, no token/room/presence disclosure). Re-ran the full `services/aster-agent` suite plus 5 new tests. | **51/51 passed, zero regressions** in the existing 32 |
| 2026-09-10 | 2 | Wrote `scripts/produce-aster-homeassistant-report.py` (private-token read with permission enforcement, `/api/states` aggregation, documented per-domain state classification, atomic mode-640 write) and its test suite against synthetic fixture data covering classification correctness, domain-allowlist enforcement, consistency with the real validator, and that no entity_id/name ever appears in output. | **13/13 passed.** Not yet deployed or run against live Home Assistant — no network path from this session |
| 2026-09-10 | 2 | Wrote `scripts/validate-aster-homeassistant-report.py` mirroring the ARR CLI validator; smoke-tested manually against a synthetic fixture report end-to-end. | Passed; exit code 0 on a valid fresh report |
| 2026-09-10 | Continuity | Created Routine `trig_01Tq9kn6TWXt9TKse9LJMUws` (every 4 hours, self-bound to this session) so a context/token-limit interruption doesn't silently stall the project; its prompt re-states this document's ground rules on every fire. | Registered; next fire 2026-09-10T08:01Z |
