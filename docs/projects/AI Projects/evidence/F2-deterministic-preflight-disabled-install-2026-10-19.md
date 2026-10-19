# F2 deterministic preflight — disabled installation result

**Date:** 2026-10-19 America/Vancouver  
**Decision:** PASS for the bounded disabled installation; F2 remains OPEN  
**Authority:** Jason approved “install and test” for the reviewed F2-only
candidate. This authority did not include capturing a backup-cycle snapshot,
invoking the archive guard, enabling a unit or timer, acquiring a lease,
stopping a service, writing a receipt or calling a model.

## Purpose

The narrow 01:10–01:19 F2 start window had twice been lost while a Codex task
performed a long interactive preflight. The candidate moves the slow,
deterministic preparation into two root-custodied host modules so a later
supervised invocation can use a short fresh final gate. It does not make Codex
scheduling an infrastructure clock and does not itself perform the scan.

## Pinned input

The platform-owned release card at commit `5e77cd7b` pins these two new files:

| Installed path | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py` | `a2324d6a5ba4869778713319a511acc207f1d8332dd1af7e4520be382cfe02fa` | `root:root`, mode `0644` |
| `/usr/local/libexec/local-ai-lease/f2_preflight_fixed_wrapper.py` | `2b381465300db3d7cc1d521123665df19ff58fad12d5cccd54720b9f89cb433c` | `root:root`, mode `0644` |

The private runtime directory is
`/var/lib/local-ai-lab/f2-preflight`, `root:root`, mode `0700`.

Before staging, the target paths and runtime directory were absent; the
existing `/var/lib/local-ai-lab` root was `root:root` mode `0700`; all six
installed dependency hashes matched the card; the lease was `ready`; and
LXCs 104, 110 and 116 were running.

## Fail-closed pre-install test and correction

The first target-Linux test attempt stopped at 7/8 passes before installation.
The missing-snapshot test expected the word `custody`, while the reader's
correct fail-closed result was `snapshot is unreadable`. The root-owned
positive round trip passed. No target module or state directory had been
installed at that point.

Platform commit `56c43bdc` changed only that test expectation; the two
reviewed module hashes remained unchanged. The corrected target-Linux suite
then passed 9/9, including the root-custody positive case.

## Installation and validation

The absent-state recovery checkpoint is retained at
`/root/aster-f2-preflight-rollback-5e77cd7b/targets-were-absent`, owned by
root and mode `0600`. The two modules and private state directory were then
installed with the pinned hashes and custody above. The same target suite
passed 9/9 from the installed paths.

A clean independent postcheck found:

- the two installed hashes and ownership/modes match the release card;
- the private state directory is empty: no captured snapshot exists;
- the lease controller reports `ready`, with no F2/archive receipt;
- no F2-preflight or `zstd -t` process exists;
- LXCs 104, 110, 114 and 116 are running;
- `aster-agent`, `aster-llama` and `aster-speech` are active;
- LXC 114's `news-aggregator-ingest.timer` and
  `news-aggregator-digest.timer` are active and enabled; and
- Proxmox `pvescheduler` and `pvestatd` are active.

The temporary host staging directory was removed after these checks. The
installed files and rollback marker were retained.

## Result and next gate

The disabled deterministic preparation layer is installed and tested without
changing production service availability or schedules. This closes only the
installation prerequisite. It does **not** close F2: no current-cycle snapshot
was captured and no three-archive integrity/timing result exists.

The next live step must have its own reviewed invocation path and current
authority. It must capture preparation evidence only after the relevant
backup/pull cycle, perform a fresh short final gate inside the allowed start
window, invoke the already installed bounded read-only guard at most once,
and retain the three exit-zero timing rows. Any drift, late start, competing
work or uncertain postcheck remains a NO-GO.
