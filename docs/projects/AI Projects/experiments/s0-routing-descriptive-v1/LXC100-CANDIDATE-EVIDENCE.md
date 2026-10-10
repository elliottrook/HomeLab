# LXC100 collector/session candidate — 2026-09-26

Status: local fixture tests passed; incomplete integration; live entry disabled.

## Evidence and scope

15 new collector/session/DNS fixture tests pass; 176 full adaptive tests pass.
The S0-specific subset passes 103 tests. All child processes were local invented
fixtures; DNS uses injected socket stubs. No SSH, LXC100 mutation, accepted-corpus
read, model evaluation, package installation or push occurred in this revision.

Fixed command catalog covers existing canary/run/stop proposals and metadata-only
health, path, canary identity, unit property and cgroup collectors. Catalog hashes
include exact source and argv. The candidate session requires the expected catalog
hash and defaults to denying process creation. Injected spawn is a trusted test
seam, not a security boundary. No arbitrary remote command/path API is exposed.

Collector child commands have a shared 12-second deadline, 4 KiB combined output
limit per command, fixed environment, kill/reap cleanup, and no stdin. The outer
candidate session caps combined output at 8 KiB and elapsed time at 20 seconds.
Tests exercise local timeout, output overflow and stderr rejection. Reading fixed
proc/cgroup metadata is not itself proven bounded under a broken kernel/filesystem.
No claim of remote execution safety is made from local fixture results.

Readiness now carries PID. Ownership binding checks the observed MainPID, unit
invocation, successful exclusive canary creation and observed device/inode values.
Mismatched PID, invocation or canary identity rejects automatic cleanup. This is
conservative candidate logic; it does not eliminate root-level replacement races.

## Unresolved gates before any live invocation

1. Integrate observation collectors with the reviewed lifecycle state machine;
   current state-machine transport still accepts only fake fixtures.
2. Persist ownership receipts and test interrupted-session recovery end to end.
3. Define safe recovery when the unit has already unloaded. Current cleanup
   requires its original invocation and therefore returns no automatic cleanup
   permission when that identity is unavailable. Do not weaken this to blind delete.
4. Establish whether actual systemd property output matches strict parsers. Expanded
   syscall groups or alternate values currently fail closed as inconclusive.
5. Review command/source/plan hashes and the full candidate before enabling any
   narrowly scoped live transport. Authorization does not substitute for readiness.

The coordinating task conveyed Jason's authorization for the exact fixture-only
probe once technically ready. Its latest instruction explicitly prohibits live
SSH/LXC100 during this candidate preparation. No broader approval, corpus run or
push is inferred. Prior manifest hashes are historical evidence at their commits;
`lxc100-candidate-manifest.json` pins this candidate's artifacts.
