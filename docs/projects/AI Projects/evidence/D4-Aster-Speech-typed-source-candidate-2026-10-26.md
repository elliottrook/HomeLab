# D4 Aster Speech typed diagnostic — source candidate

**Date:** 2026-10-26  
**Scope:** offline source and synthetic tests only  
**Production effect:** none

## Selected second diagnostic

The second named diagnostic is `aster.speech`. It is a useful, distinct Aster
function backed by the existing bounded LXC116 health probe. Its current
Doctor check already resolves to one pass/fail result covering the canonical
voice, synthesis canary, Home Assistant Wyoming path, HTTPS ingress and
Companion identity discovery. It therefore does not require interpreting a
human summary to identify the check.

## Source candidate

The report builder now has an opt-in `--catalogue-output` path. When selected,
one fresh Doctor invocation receives a separate inherited catalogue
descriptor and the same run ID used for schema-2 evidence. Doctor emits only
the two closed IDs `aster.agent_inference` and `aster.speech`; the catalogue
builder rejects every other ID.

The schema-3 file:

- is bound to the exact aggregate report digest and generation time;
- contains only check IDs and allowlisted states;
- is written atomically at mode 0600 locally;
- publishes only to the fixed `diagnostic-catalogue.json` path when the
  catalogue option and existing publish option are both selected; and
- remains absent during ordinary or current schema-2-only collection.

The existing schema-2 `aster.agent_inference` file and fixed Doctor capability
are unchanged. No schema-3 consumer, caller, broker grant or model route is
created by this candidate.

## Validation

- report-builder structured/catalogue fixtures: **7/7 passed**;
- combined catalogue and fixed-Doctor boundary suite: **35/35 passed**;
- `bash -n scripts/doctor.sh`: passed;
- Python compilation of the producer and catalogue module: passed.

The fixture proves both named states share the aggregate digest and generation
time, while private human words remain absent from the catalogue. Existing
publish-fixture coverage also proves a schema-2-only run sends no catalogue.

## Result and next gate

**PASS as an offline source candidate.** No live file, service, schedule,
identity, grant, route or model request changed.

Before production use, freeze exact source hashes and target paths, validate
the embedded fixed-path writer on target Linux, preserve the current producer
for rollback, and prepare an independently reviewable inactive/cutover card.
Activating catalogue production or a new speech reader remains a separate live
effect. A speech capability must still expose only this one named state and
retain authority `not-granted`.
