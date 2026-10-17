# F2 guarded observer — disabled installation result

**Observed:** 2026-10-16 America/Vancouver (postcheck 2026-10-17 01:54 UTC).
**Scope:** Jason approved one bounded stage/test/conditional three-path
installation in this Stream A chat. This is not approval for a live F2 scan,
receipt, lease or full-stop drill.

## Preflight and source custody

Source was frozen at local `codex/aster-lease-compat` commit `339b554e`;
the one-use installer and rollback tests at `7e6ea99b`. The release card is
`F2-READ-ONLY-OBSERVER-RELEASE-CARD-20261016.md`. The six source/test files
were placed in root-owned mode-0700
`/var/lib/local-ai-lab/f2-stage.JBV2aDou`, with source archive SHA-256
`17ca0fa3a604afff53fd264583b80d3f6c039ffbeef2dca799c4ae7fee23e00c`.
Each extracted file matched its card pin. The installer and its synthetic test
matched card hashes `00e21346…` and `41c1fa76…`; both staged files were
root:root mode 0600.

Before the install, Proxmox reported `local-ai-lease status` ready, no
whole-host/application lease or archive receipt, no backup/scanner process,
load 1.54, and LXC104/110/116 running. The two replacement files matched
their recorded old hashes and modes; the add-only F2 guard path was absent.
Both watchdog/owner-heartbeat timers were disabled and inactive. LXC114 News
ingest/digest timers were active and enabled; the fixed Proxmox backup job
remained enabled at 00:30 on `backups`.

On target Linux, the staged F2/manual/producer suite passed **23/23**,
including a synthetic child-process termination check. The one-use
installer's disposable-path suite passed **4/4**, exercising success, state
refusal, old-byte/add-path drift, and interruption before each of three
file writes. These tests made no archive, model or live lease call.

## Exact installed result

The installer held the common state-directory lock, checkpointed both old
files and atomically wrote only these three root-owned paths:

| Path | SHA-256 after install | Mode |
|---|---|---|
| `/usr/local/sbin/local-ai-lease` | `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c` | 0750 |
| `/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | 0644 |
| `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` | `d50ee2207bc4185db266ad01af540b9b719397dec3855ee579ee18f983a3535d` | 0644 |

The root:root mode-0700 checkpoint is
`/var/lib/local-ai-lab/f2-disabled-checkpoint.u_3tqmdn`. Its two originals
are mode 0600 and retain SHA-256 `f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23`
and `7e9b82a0c5216aad99ca1350849abb486a482586548c00ae6d7b6f309a1516c8`.
It is left in place for exact rollback; the previous seven-path checkpoint is
also unchanged. No current bytes were rolled back because postchecks passed.

Installed imports of guard, producer, observer and host exclusion passed.
The manual status remained `ready`. Invoking the guard **without** its
separately gated flag returned `{"state":"disabled","scan":"not-attempted"}`.
All four watchdog/heartbeat units remained inactive; their two timers stayed
disabled. LXC104/110/116 and LXC114 remained running, the LXC114 News timers
remained active/enabled, and the fixed 00:30 Proxmox backup configuration was
unchanged. No lease/lock/receipt path or backup/scanner process was present.

## Decision and remaining gate

**Disabled installation: PASS. F2 timing/integrity: NOT RUN / NO-GO.** This
does not establish a complete current-cycle 104/110/116 archive check or
trusted F3 receipt. A first F2 scan would require fresh cycle-specific
backup/task/volid/load preflight, a supervising operator, and separate dated
approval. No timer was enabled, no archive scanned, no service stopped, no
model called, and no backend or schedule changed.
