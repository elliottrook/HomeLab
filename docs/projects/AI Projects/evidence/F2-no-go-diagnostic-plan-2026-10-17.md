# F2 October 17 NO-GO — diagnostic plan for a later cycle

**Status:** analysis only. The October 17 one-cycle scan approval was consumed.
No retry, host change, receipt or drill is authorized by this plan.

## Known and unknown

The fixed 00:30 Proxmox backup and 01:00 TrueNAS task 1 completed. The
operator's read-only preflight found the expected three current-cycle archive
identities, installed hashes, quiet host, ready lease and unchanged schedules.
At about 01:10 the installed one-shot guard returned `F2NoGo` without archive
rows. Its current failure output does not distinguish a guard preflight
denial, observer failure, archive probe failure, or result-shape rejection.
Later read-only predicate checks passed, but they cannot identify the failed
instant or prove that any `zstd` test completed. Do not infer archive corruption
or a controller bug from this result.

## Review order before any new release

1. **Offline deterministic replay:** exercise the exact installed-source
   preflight and observer code against sanitized, pinned synthetic responses
   for the fixed backup, guest logs, task-1 job shape, archive identities and
   clock boundary. Cover pass and one-denial-per-gate cases; emit fixed stage
   codes only. Do not replay private output or current archives.
2. **Diagnostic boundary:** independently review source-only commit
   `e5963762`, which adds `preflight` / `observer` / `result` failure phases.
   A phase is a hint, not a success receipt or precise cause. Check that child
   output, paths and exception messages still cannot reach the model/chat.
3. **Target-Linux candidate validation:** only after a new hash-pinned card,
   test installed-path imports, custody, process-group termination and
   fail-closed behavior on Proxmox with synthetic files. Preserve rollback
   bytes and leave timers/effects off. No archive scan is part of this step.
4. **Future one-cycle decision:** require a fresh backup/pull chain, quiet-host
   and lease evidence, a reviewed operator-supervised scan card with bounded
   deadline, and separate approval. Record start/end and each archive result
   only if the guard returns a complete three-row result. On any uncertainty,
   stop without retrying in that cycle.

F2 remains **FAILED/UNKNOWN for October 17**. F3, the full-stop drill and A1
cannot inherit any proof from this attempt. The platform owner controls host
release; Stream A maintains the evidence and comparison boundary.
