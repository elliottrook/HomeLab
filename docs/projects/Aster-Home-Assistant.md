# Aster Home Assistant Advisor

> Status: Active — implementation and graduation in progress
>
> Owner: Jason
>
> Started: 2026-09-10

## Purpose

Graduate Aster into a source-aware, privacy-preserving Home Assistant advisor
for this instance without granting general control. The ARR project is the
template; Home Assistant receives its own curriculum, sanitized live report,
adversarial suite, recovery proof and explicit authority boundary.

## Resume contract

This file is the durable checkpoint. After any interruption: inspect Git status
and the latest commit; read the unchecked boxes and evidence log; rerun local
tests before the next unchecked item. Synthetic reports and prompts are allowed
when production has no safe fault. Never copy credentials, raw states or private
entity data into Git or evaluation output.

## Milestones

- [x] M0 — Inventory reviewed sources, authority, integrations, automation
  ownership, backup/recovery and exclusions.
- [x] M1 — Add the reviewed curriculum, strict report schema and versioned
  source-aware/adversarial evaluation set.
- [x] M2 — Deploy an operator-produced report and give Aster read-only access
  only to the validated fixed path.
- [ ] M3 — Deploy the policy/knowledge changes with rollback copies and verify
  local/deployed unit tests.
- [ ] M4 — Pass the Home Assistant graduation suite twice plus legacy Aster and
  ARR regressions; use synthetic report states for unavailable production faults.
- [ ] M5 — Verify service health, report freshness, backup coverage and rollback;
  close the project and move it under `completed projects/`.

## Graduation gate

All ten Home Assistant cases pass twice on the production model; strict report
tests reject stale, malformed, writable, symlinked and extra/private data; legacy
security/provenance suites remain green; Aster has no HA credential or mutation
tool; the deployed source and knowledge snapshot have rollback copies; evidence
and recovery steps are recorded.

## Evidence log

| Date | Gate | Evidence | Result |
|---|---|---|---|
| 2026-09-10 | Discovery | Read-only `ha --raw-json` through VM 103's guest agent | Core 2026.9.1 and Supervisor 2026.09.0 healthy/current; Matter Server running; TrueNAS backup mount active; Resolution lists empty |
| 2026-09-10 | M0/M1 | Added reviewed reference, strict aggregate schema/producer, privacy tests and ten-case suite | Local implementation ready; no credential, entity state or mutation capability added |
| 2026-09-10 | M2 | Installed a root-owned five-minute producer on Proxmox using only guest-agent `ha --raw-json`; delivered mode-640 `root:aster` output to LXC 104 | Live report is 475 bytes and contains only approved versions, booleans and aggregate Resolution counts; no HA credential or direct Aster route exists |
