# Stream A evening execution decision — October 14 Vancouver

Status at 21:00 PDT: **no live test admitted; the scheduled Stream A checks
are read-only**. Reassess from live state at the time, never from this note
alone.

## What changed from yesterday's expectation

The October 13 B60 readiness checkpoint at `57c551e3` explicitly left the
shared lease, independent watchdog, exact restoration, Aster-path benchmark
admission and paused schedule open. Describing the remaining work as merely
"waiting for evening lab time" was inaccurate. October 14 disabled-install
work closed only an installation prerequisite. It did not prove the integrated
controller or backup provenance.

Two measured blockers now make the proposed 03:10 full-stop card NO-GO:

1. The installed old manual controller writes a lease schema rejected by the
   installed independent watchdog. The platform owner's later source-only
   candidate and tests do not replace that installed controller.
2. The fixed serial `zstd -t` check passed the 1.957 GB LXC104 archive in
   17.4 seconds, but did not finish the 43.585 GB LXC110 archive within its
   300-second per-archive limit. LXC116 was not reached. This is an unverified
   archive, not evidence of corruption. The planned 03:05–03:10 integrity
   preflight is therefore too short for the installed method.

A bounded second read of the October 14 LXC110 archive later passed in 367.36
seconds; LXC116 passed in 31.25 seconds. Those readings make the five-minute
slot conclusively too short, while the 110 re-read may have benefited from
cache. The exact October 15 archives remain unverified until scanned.

Later source-only progress: the platform owner independently reviewed and
committed the retained-integrity candidate through `b5ec9eb2`. Its explicit
adapter path checks current Proxmox artifacts, TrueNAS task order, the exact
LXC110 mirror and a root-owned retained archive receipt; the default path is
unchanged. The local suite reports 150 tests, 2 skipped. Read-only Proxmox
checks found Python 3.13.5, the expected `ionice`/`nice`/`zstd`/`pvesh`/
`pvesm` tools, a root-owned 0700 `/var/lib/local-ai-lab` directory and an
unchanged single-link Oct14 LXC110 archive. The candidate is **not installed
or called by the host**. Source tests and host prerequisites do not close the
target-Linux integration, fresh-cycle timing or live recovery gates.

The full-stop drill and application-only A1 benchmark are mutually exclusive
within one backup cycle under the platform owner's current card, even if
full-stop restoration succeeds. A1 has independent missing gates: a trusted
current-cycle exact Mac source/destination receipt, restricted Mini-to-host
identity, admitted application-only lease/watchdog and test-only ingress.
The nine-file source snapshot was captured before tonight's 03:00 Mac pull;
its destination comparison remains a read-only future-cycle preparation step.

## Actual schedule and decision points

| Local time | Observed configuration or task | What it can establish |
| --- | --- | --- |
| 00:30 | Enabled Proxmox all-guest backup job | Completion still must be observed; job success alone is not archive integrity. |
| 01:00 / 02:00 / 03:00 | Enabled TrueNAS guest, LXC110 and Mac pull tasks | Each actual current-cycle result must be checked. Mac task success is not exact-subset equality. |
| 01:10 | Active one-time Stream A read-only cold-archive timing check | Runs only after backup and task 1 complete, with low I/O priority and strict deadlines; its result is not a trusted admission receipt. |
| 03:05 | Active one-time Stream A read-only preflight | Compares current evidence and marks NO-GO if any source or controller gate is absent. It cannot start a lease or model call. |
| 03:10–03:30 | Platform owner's *proposed*, currently NO-GO full-stop effect window | No effect automation is scheduled by Stream A. A new hash-pinned, tested, approval-ready card and separate live authorization would be needed. |
| 03:40 | Active one-time Stream A read-only post-window check | Records whether a separately approved drill actually ran and whether exact restoration holds. It cannot retroactively authorize a run. |
| 04:15 | Outer restoration/reconciliation limit | Not a spare interval for an archive check or a first A1 batch. |

These app automations are follow-up reminders and checks, not a hard real-time
controller or an independent safety mechanism. A missed/delayed heartbeat must
not silently admit a test. The obsolete runner remains disabled.

## Minimum route to a live result

For **full-stop**: retain a current-cycle archive-integrity receipt bound to
the actual 104/110/116 archive identities and measured within a safe earlier
window; install a schema-compatible, source-bound acquisition path disabled;
run target-Linux producer-to-watchdog decode and post-stop quiescence tests;
freeze a revised card with exact runtime/schedule restoration and rollback;
then obtain its distinct live approval. If any item is absent, record NO-GO
and leave production running.

For **A1**: use a later backup cycle or an explicitly revised platform scope.
Its own trusted backup subset producer, restricted identity, isolated test
gateway, application-only lease, independent watchdog and 20-minute batch plus
restoration reserve must pass before the first model request. Source/destination
equality after tonight's Mac pull would close one provenance observation only.

**Deadline assessment:** both live proofs cannot be completed by the October
15 morning cutoff under the current mutually exclusive one-cycle rule. Even
one full-stop proof is conditional on replacing the two measured blockers
before the live card is frozen. No completion date should be claimed from the
clock or a green source-only test suite.
