# Aster Lab Hours RC1c — October 29 exact-cycle card

Status: approval-ready; not installed or enabled by this card.

This is the release-candidate test for the separate **Aster Lab Hours**
project. It does not depend on F2, F3, F4 or F5 success and does not create or
convert any archive receipt. The only backup dependency is the source
producer's direct proof that the fixed Proxmox 00:30 job and current-cycle
104/110/116 archives completed.

## Candidate and measured evidence

RC1c is the October 27 two-pass full-inference candidate plus explicit EPUB
narration isolation. Two earlier October 28 attempts failed closed at the EPUB
service postcheck and restored production. The final unchanged candidate then
completed twice at 09:08 and 09:11 PDT. Each pass:

- masked/stopped Aster Agent, accepted llama/SYCL, Speech, both News timers,
  the EPUB worker timer and its active worker;
- proved the B60 holder boundary and ran the fixed three authenticated,
  tool-free lab requests;
- removed the lab scope/listener/process;
- restored the exact accepted model/backend/authentication and all services;
- resumed the EPUB timer and worker; and
- left no lease, state, lock or guardian.

The installed suite passes 73 tests on Proxmox Python 3.13. The relevant
installed source hashes are pinned in
`lab_hours_exact_cycle_runner_20261029.py` and are rechecked before any effect.

## One exact run

After approval, install the runner as root-owned mode 0644 in the existing
root-only pilot directory and install the exact service/timer from this
packet. Enable only `aster-lab-hours-20261029.timer`, scheduled for **04:05
America/Vancouver on October 29, 2026**. The date-specific runner refuses a
second attempt, rejects installed drift, an active shared lease/lock, or any
competing F2/F3/F4/F5, backup, archive scan or maintenance process.

The runner arms the independent deadline guardian before the first effect,
creates a new owner scope, runs RC1c, and writes only root-owned bounded
evidence beneath
`/var/lib/local-ai-lab/lab-hours-attempts/night-rc1c-20261029/`. On owner
failure with durable state, it leaves the guardian active and waits for its
bounded recovery. A terminal record contains the first failure phase and
class, a bounded specific failure code, candidate hashes and whether production was restored. It never retries
the transaction.

## Historical failure closure

The exact runner was audited against every missed or failed October 19–28
cycle before activation. Lab Hours does not consume F2, F3, F4 or F5
artifacts, so the former mirror-ordering, scanner PATH, coordinator/child API,
installed-pin, observer-exit, receipt-freshness and handoff-window defects
cannot block or partially promote this run. It still rejects any of those
processes or exact-cycle units if they overlap.

The wrapper closes the operational failures directly: a date-specific timer
is installed and verified in advance; starts outside 04:00–04:15 PDT fail
closed; installed files are hash-pinned; an existing attempt, lease, lock,
backup, archive scan, evidence process or workload-transition process blocks
effects; and the current-cycle Proxmox backup/job proof is checked by the
owner before isolation and again by the production validator. The EPUB timer
and static worker are part of the fixed drain and restoration inventory.

Every failure retains a bounded `first_failure_phase`, `failure_class` and
specific `failure_code`. If an owner transaction fails, disappearance of its
state file is not recovery proof: the wrapper runs the full production
validator after guardian recovery and records `production_restored=true` only
when that validator passes. The transaction has no automatic retry.

## Effect and exclusions

This run intentionally interrupts Aster Agent, the accepted llama service,
Speech, News and EPUB narration while the fixed lab workload runs. It restores
them in the same transaction. It does not change a model, backend, credential,
GPU binding, backup, schedule outside its own exact timer, F2/F3 evidence, or
remote Git state. It does not reboot the host or any guest.

If successful, remove the spent exact-date service/timer after observation and
retain the terminal evidence. If failed or uncertain, do not retry; preserve
the attempt, reconcile production, and use its first failure phase for the
next release candidate.
