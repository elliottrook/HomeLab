# SA3 candidate-g unhandled exception-class correction — 2026-11-04

## R4 evidence

Fresh booking `aster-stream-a-sa3-envelope-20261104-1400-r4` claimed exactly at
14:00:00 and ended NO-GO at 14:03:13, after 193 seconds. The terminal state was
`OWNER_TRANSACTION_FAILED_RESTORED`, first phase `owner-transaction`, with
`production_restored=true`. No result file was retained.

Despite the installed line-oriented host parser, the retained owner error was
still `candidate-g listener exited nonzero: unclassified guest failure`. This
proves the guest wrapper emitted no standalone bounded JSON code on that path.
R4 is spent and must not be retried.

Independent postchecks found the lease ready; Doctor healthy with no codes; no
drain/shared lock, listener, transient scope or candidate process; LXC104/110/116
and all required Aster, accepted llama, Speech, News, EPUB, Doctor and Proxmox
services healthy; core service restart counts remained zero.

## Deterministic gap

The wrapper serialized only `GuestError`, `OSError`, `ValueError`, and
`urllib.error.URLError`. Any other ordinary `Exception` escaped as a traceback.
The host correctly found no bounded JSON line and conservatively classified the
failure as unclassified. Required capture cleanup then removed the raw guest
traceback, so R4 cannot establish its exact exception class.

## Source-only correction

The wrapper now catches a final `Exception` boundary and emits only:

`candidate-g guest exception-class:<ClassName>`

The class name must match `[A-Za-z][A-Za-z0-9_]{0,63}`; otherwise it becomes
`Exception`. The exception message is never emitted. `BaseException` remains
outside the catch, so interrupts and process-control signals are not converted
into workload failures.

Corrected wrapper SHA-256:
`626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe`.

Focused platform tests pass 28/28. The wrapper-specific suite passes 4/4 under
the Proxmox host's Python runtime and proves that a synthetic `KeyError` retains
only `KeyError`, excluding its private message. The exact target staging
directory was removed after proof.

## Boundary

This correction is source-only. It authorizes no install, booking, retry,
model request, restart, blind review, route or promotion. A reversible one-file
inactive installer and installed-path proof are required before any fresh
candidate-g booking.
