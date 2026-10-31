# November1 preparation — cross-host backup clock hazard

## Finding and effect

**Do not arm the next qualification assuming01:00/02:00/03:00 schedule labels
mean the same instants across hosts.** No model or restore-only trial is armed
by this preparation. This is separate from October31's unit-capture refusal.

Read-only control-plane ownership checks found no lease/drain/operation markers
or common directory-flock holder before the following metadata checks.

| Source | Actual observation | November1 mapping |
|---|---|---|
| Proxmox `/usr/share/zoneinfo/tzdata.zi` | `# version 2026c` | Vancouver03:10 is `2026-11-01T03:10:00-07:00` |
| TrueNAS same metadata path | `# version 2025b` | Vancouver03:10 is `2026-11-01T03:10:00-08:00` in its database |
| TrueNAS `system.general.config` timezone only | `America/Los_Angeles` | Los Angeles03:00 is `2026-11-01T03:00:00-08:00` on both hosts |

TrueNAS task1 is enabled daily01:00, task3 enabled daily02:00 and task2
enabled daily03:00. Selected sanitized projection from `rsynctask.query` plus
timezone, canonical sorted compact JSON SHA-256:
`15ea1c78730f5121b4cff574d1577a72af21617326d1c0fb75b6194b5b62227a`.
Only timezone and selected IDs/enabled/schedule were emitted, never credentials
or full configuration. No changes or immediate pulls were invoked.

Using the observed source-local offsets and Proxmox's actual timezone rules:

| TrueNAS task / source wall clock | Possible epoch(s) | Proxmox Vancouver clock |
|---|---|---|
| task1 guest pull /01:00 LA | `1793520000`, `1793523600` |01:00 or02:00 UTC−07 |
| task3 LXC110 mirror /02:00 LA | `1793527200` |03:00 UTC−07 |
| task2 Mac pull /03:00 LA | `1793530800` |04:00 UTC−07 |

The ambiguous first-hour rows enumerate timezone possibilities, **not proof
the TrueNAS scheduler will dispatch twice or which fold it chooses**. That
policy has not been measured. The unambiguous Mac pull is already decisive:
it is scheduled after the booked03:10 qualification start, independent of the
first-hour policy. November2 remains one hour shifted; this is not merely a
one-night repeated-hour nuisance.

Actual next root-custodied record:
`/var/lib/local-ai-lab/reservations/records/b60-exclusive-20261101.json`,
SHA-256 `55ed0e33edf8c1db637cf6cc357d2250af2599aabb4f3b4fb4b0d898a3116d4f`.
Owner b60-stream-a, kind exclusive-stack, state reserved, start1793527800,
end1793530500 (03:10–03:55 Vancouver UTC−07),900-second buffer. Its activation
path is absent. Mac pull starts five minutes **after** the booking ends.
Capacity reservation is not a future activation or automatic experiment.

Changing only the TrueNAS timezone label to Vancouver is **not a verified
repair**: its currently observed older timezone database still gives
Vancouver UTC−08. Conversely, moving the lab past04:00 consumes the required
restoration margin and protected04:15 boundary; do not silently extend it.
No global timezone/package update or backup-schedule rewrite was authorized
or performed by this preparation heartbeat.

## Offline instrumentation and regression evidence

`scripts/b60-inference/backup_clock_projection.py` is a pure calendar audit of
sanitized selected daily schedules. It enumerates valid UTC folds, rejects
nonexistent times, checks exact contract instants, fails closed on incomplete,
duplicate, disabled or unsupported schedules, and never grants admission.
Its timezone database is an explicit environment dependency: a local aligned
projection cannot authenticate a remote database or scheduler. The observed
host-version mismatch above therefore remains an independent gate.

Eight synthetic tests cover October31 alignment, November1/2 divergence,
aligned-database counterfactual, malformed/duplicate/disabled/non-daily inputs,
no input mutation and nonexistent spring time. These are not live backup runs.

Implementation commit `546d85b2c` adds two synthetic regression cases to the
exact existing source adapters. Both `_schedule_ok` and
`validate_backup_sources` reject the projected future Mac-pull completion at
the actual03:10 booking start. No admission code or schedule is relaxed.
Pinned adapter bytes:

- `scripts/local-ai/fixed_source_adapters.py`:
  `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9`.
- `scripts/local-ai/full_inference_lab_sources.py`:
  `920d2ed171d314a6cb346032651c24a7972e51b2a91c2bb2892dcd9419c50d48`.

The portable test patch is under
`scripts/b60-inference/backup-clock-20261101/`; apply after the existing
`d7af14802` diagnostic candidate. Patch SHA-256:
`372a4941bec46071b69495d54dd1ca5c140fca62a39df063113d2a2c48566382`.
Calendar projector SHA-256:
`b497213c504e2956820b974f25a317fa3cc27df03060514fe8ca9aaded08f0df`.
Full implementation commit `546d85b2ce18ead0eab42011e5c2d726be48c20a` and
independent replay have identical tree
`aaf1e1a6367c8855fdb6f38666bff2022b9dbc56`. Both136 Lab Hours tests and115
B60 tests pass against this exact dependency root with no skips. Nothing is
installed; these results grant no live admission or qualification.

## Next action / authority boundary

Before any operational arming: reconcile timezone versions, actual epoch
semantics of the three selected pulls, ambiguous-hour dispatch, adjacent
backup/snapshot/cron consumers, and a fresh full chain completing before the
unchanged booking. Select a bounded, source-reviewed schedule/clock correction
under the owning operational authority with rollback; do not improvise a
global NAS timezone or package change from the prior single-mirror approval.
That review can proceed safely without a model or exclusive stack use.

Separately, the installed source rejects replacement by the existing dormant
installer (`EXISTING_DORMANT_SOURCE_DRIFT`). The optional backup/unit diagnostic
candidate therefore needs a reviewed source-update transaction or versioned
installation before a new activation can reference it. Do not instruct the
old no-overwrite installer to deploy changed bytes, or mutate old profiles to
hide drift. Retain all October30/31 evidence and accepted recovery artifacts.

Only after clock/source gates are resolved should an operational continuation
prepare fresh five-guest metadata plans, exact no-model profile and future
dated clocks, then independently verify actual arming. Recovery and owner-loss
qualification remain prerequisites for model experiments. This is a genuine
technical preparation gate, not missing repeated model permission, peer
unresponsiveness or programme completion. No background execution is claimed.

## Peer receipt refresh

Authoritative Forgejo fetch finds no new peer replies. Read BOTH liaison tips
and platform/booking records, not main. Exact commit/path/hash receipts remain
those in [October31 reconciliation](qualification-no-go-20261031.md), except
the B60 received tip is now `cc01ec2beaf619fdcdbb1f64d6262a72a543e641`, path
`docs/projects/B60-Inference-Engineering/qualification-no-go-20261031.md`,
SHA-256 `e82d8be431dc041a28216ce38d0b6ddf1dbaf2148a52344e434db80b54ef9e91`.
Adaptive remains `d88f8239b`, platform `6fb0207f`, booking owner `5a9c3471`.
Publish only the bounded sanitized liaison evidence under standing authority;
verify the automatic GitHub mirror read-only. A push is not peer reading.
