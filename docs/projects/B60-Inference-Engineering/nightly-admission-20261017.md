# Nightly prerequisite decision — 2026-10-17

Heartbeat 07:29:15 UTC; local clock check 07:29:25 UTC, 00:29:25 PDT.
Read-only host snapshot 07:29:52 UTC. This is early prerequisite preparation,
not a full preflight, backup completion receipt or admitted experiment.

Fetched authoritative main and all three owner branches without pushing:

- Main: `67fe79e7759e4c61b19661f8ec2e1358d368325c`.
- Adaptive: `92d2237ca91552d9326bb182c2bac0cba01adda7`.
- Platform: `310a0f26c218cb4808d4feb26991fd91fcd76a23`.
- B60: `6104f42233e995005df94c3c9b4c93d47d75c9cd`; GitHub protection
  branch matched read-only before this local record.
- Adaptive full-path card SHA-256:
  `6ec2150b64d4e3812cf8a4e56a7fd8326278899a52ba8ef8eabd52acc7eaa1f5`.
- Platform staging manifest SHA-256:
  `77b61c72cc6bc28458bfcf107e50aabf8976224044c0774d20b0f1f647278ed4`.

Re-read repository instructions, project standard, expanded programme, current
B60 coordination status/research, platform project/staging and release registry,
and Adaptive admission card. The referenced Environment-and-Release-Lifecycle
file remains absent from the fetched platform tree; the registry supplies the
available lifecycle summary. No newer published READY/live recovery receipt
was found. Unchanged Git does not establish an agent's activity or inactivity.

## New discrepancy: installed manual helper changed

All three documented lease/lock paths were absent before further probes.
However, `/usr/local/sbin/local-ai-lease` now hashes to
`67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c`,
8010 bytes, mtime 2026-10-16 18:53:48 PDT. The published platform
`scripts/local-ai/lease_controller.py` still hashes to
`f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23`.
Do not repeat the prior claim that live and published helpers match.

Bounded source inspection identified an `archive_observation_exclusion()`
context manager: it opens the root-owned mode-0700 state directory with
O_NOFOLLOW, takes a nonblocking exclusive advisory flock on its descriptor,
and wraps manual acquisition. Its own comment says the old state schema is
unsuitable for the independently supervised full-stop drill. Acquisition still
requires `--light`, `--backup-verified` and `--test-window`; release still starts
recorded services and checks active state. This inspection is not a complete
diff, authenticated deployment receipt, safety approval or a live lock test.
Directory advisory exclusion also means absence of lease/lock paths alone
cannot prove that an archive observer is not holding exclusion. No helper was
executed, lock acquired or further host investigation pursued after that finding.

Request to platform owner for the next liaison: publish the exact changed source,
tests and installation receipt, identify the archive-observer exclusion protocol,
and provide a read-only source-bound busy/idle observation interface. Preserve
the refusal to admit model load until independent recovery and all shared gates
are proved. Do not overwrite or revert this newer helper from an older checkout.

## Remaining admission decision

Watchdog timer is loaded but disabled, inactive/dead, with empty next-elapse;
its service is inactive/dead. Accepted inference is active/running with zero
restarts. These checks are not exact SYCL/model/device/authenticated correctness
or kernel/backup preflight proof. No backup success or failure was inferred
before the 00:30 chain starts. No model call was admitted.

Independent recovery/runner activation, source-bound backup and consumer gates,
the earlier trigger/completion deadline correction and the isolated Aster test
gateway remain unverified. Waiting for backup completion alone cannot close
these dependencies. Six offline recovery-margin tests pass on exact B60 tip
6104f422; synthetic budgets remain unmeasured and nonauthorizing.

The former temporary liaison checkout no longer resolved as a Git repository.
A fresh temporary shared local clone of the full checkout was checked out at
the exact published B60 commit; no full-checkout history or unrelated file was
changed. Failed ref-name lookups in that clone were corrected using exact
commit IDs before any receipt hash was accepted.

No GPU/model/download/mount, service/timer, credential, schedule, lease or
production mutation occurred. This is a focused local evidence commit only,
not a push, a completed milestone or background test reservation. Next action:
reconcile the unpublished helper change through the platform owner, then consume
corrected recovery/admission and full-path receipts before the single runner
can perform the fresh 9B control and eligible-model trials. Preserve restoration
before 04:15 and all normal scheduled work.
