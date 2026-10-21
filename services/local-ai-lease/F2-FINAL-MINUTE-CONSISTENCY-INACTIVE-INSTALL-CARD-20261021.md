# F2 final-minute consistency correction — inactive install card

Status: source-only HOLD. This card records one bounded correction for review;
it authorizes no install, activation, retry, reschedule, scan, receipt, lease,
service stop, model call, or remote push.

## Why this correction is required

The 2026-10-21 cycle failed closed in prepare because the 02:00 LXC110 mirror
did not yet exist. That mirror remains deliberately deferred to F5. A separate
latent mismatch was also found: the installed coordinator schedules final at
01:20, while the preflight final guard and observer accepted only 01:10–01:19,
and the retained producer used an exclusive 01:20 upper bound. Installing only
the mirror deferral would therefore still fail at final.

The combined source correction makes the chain internally consistent:

| Component | Fixed window |
|---|---|
| F2 prepare/coordinator | 01:15 Vancouver |
| F2 final guard | exact 01:20 Vancouver |
| Observer start | exact 01:20 Vancouver |
| Retained producer start | 01:20–01:29 Vancouver |
| Observer/producer hard deadline | 01:40 Vancouver |
| F5 mirror gate | after the scheduled 02:00 LXC110 mirror |

## Exact source replacements, not yet installed

Preserve each current installed file as a root-owned 0600 rollback checkpoint,
then replace only these three files after a fresh bounded approval. The current
coordinator remains unchanged and is already aligned to 01:20.

| Installed path | Current installed SHA-256 | Corrected source SHA-256 |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py` | `a2324d6a5ba4869778713319a511acc207f1d8332dd1af7e4520be382cfe02fa` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` |
| `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` | `6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f` | `2af6689b82dce85d4a1856ffb6803269a5e2a20bee286012ff92faf9f925578e` |
| `/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | `5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf` |

The live installed hashes must still be re-read immediately before any future
replacement. No installation is part of this card. Proposed checkpoint location:
`/root/aster-f2-window-consistency-rollback-<new-source-short-hash>`.

## Required validation before any future install

On target Linux, privately validate the exact source set with compile/import
and focused tests. The validation must demonstrate that 01:20 is accepted,
01:19 and 01:21 are rejected, a 01:15 snapshot remains fresh at 01:20, and
the observer/producer deadline is exactly 01:40. Do not run the observer,
producer effects, scan, receipt, lease, timer, or service.

Before installation, re-read all installed hashes and custody, verify the
coordinator pin remains `fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356`,
and preserve the three old bytes before replacement. The exact three-file
replacement requires its own fresh approval; timer activation or date
rescheduling requires a separate approval.

Rollback is restoration of only those three checkpoints after stopping any
future date-specific candidate units, without clearing terminal state or
retrying the failed 2026-10-21 cycle.
