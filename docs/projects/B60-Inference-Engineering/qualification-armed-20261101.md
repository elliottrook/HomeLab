# November1 restore-only qualification — operationally armed

Jason explicitly requested finishing the production source adapter and clock
reconciliation, then arming the next qualification rather than stopping at an
offline milestone. This record reports the completed operational work, not a
preparation-only heartbeat or a successful future restoration claim.

## Clock reconciliation completed

TrueNAS's installed2025b database cannot represent the newer Vancouver rules.
Used its supported `system.general.update` API to set only the timezone to
`Etc/GMT+7` (fixed **UTC−07**, matching Proxmox/Vancouver's observed2026c rules).
No package, driver, boot, credential, backup task, snapshot, scrub or cron
schedule definition changed. No immediate pull or backup was requested.

Before the change inspected all cron/snapshot/scrub/replication/rsync schedule
metadata. No replication tasks exist. Existing nominal task clocks are kept
on household Vancouver time instead of shifting one hour with Los Angeles.
There was no wall-clock jump at the change, as the old/current offset was also
UTC−07. The reviewed supported API reloads timeservices and restarts cron and
updates zettarepl's timezone. Cron uses `KillMode=process`; its direct-child
inventory was empty before the update. No AI service was stopped/restarted.

Protected timezone/schedule checkpoint and result on TrueNAS:

| Path | SHA-256 |
|---|---|
| `/root/b60-clock-20261101-v1/checkpoint.json` | `d499d4e5f55fd6b183616896d06c4abd041bc270ceecd94397320fd58be17e58` |
| `/root/b60-clock-20261101-v1/receipt.json` | `82967f47bcb716c3cc36207a3989075520021ac9863cd1ba4bda5879bd204f50` |

Both are root-owned0600. All inspected task schedules compare identical
before/after; the complete general-settings comparison changed only timezone.
Independent read-back: timezone `Etc/GMT+7`, system offset−0700, cron active.
The existing Proxmox fixed TrueNAS observer independently reads enabled task1
01:00, task3 02:00 and task2 03:00. Their November1 epochs are1793520000,
1793523600 and1793527200 respectively, before the03:10 booking. This verifies
clock alignment, **not** future successful completion or contention absence.
Existing Sunday scrub/storage work remains untouched; fresh runtime gates
must still refuse if backup completion, resource or timing evidence is unsafe.

Clock rollback, if needed, is a reviewed timezone-only API change back to the
checkpoint value; it would restore the mismatch and require lab admission
closed. Do not perform it during an active transaction or leave future jobs
armed against an unreviewed clock change.

## Production source adapter completed and exercised

Implementation `d6e8aa6d8f3df4bb0499eef75387ea9df5965a1a` adds the guarded
host adapter/CLI and actual filesystem operations. It holds the common host
directory exclusion across the whole transaction, refuses lease/drain/operation
markers, active/recovering owners/guardians, future armed qualification clocks,
unrecovered session states and claimed ledger records. Strict source/custody
checks precede protected file checkpoint capture. Only the two reviewed
diagnostic modules may be atomically replaced, with exact expected-byte
comparison, full dependency-map proof, directory fsync and isolated import
verification. Recovery verifies protected old bytes/metadata before restoring;
unknown drift is retained and refused, not overwritten.

163 Lab Hours tests,10 dormant-installer tests and115 B60 tests pass against
the exact independent replay; trees equal
`100534e5e1099e70312bb7a25039daf7b80d3a15`. Five new host-adapter tests use real
disposable source files/checkpoints and actual child termination after either
atomic replacement. Those five also passed on Proxmox before target changes.
They fake host-idle proof only in the disposable fixture; the actual deployment
used the real common lock/metadata guards and root-protected readers.

Exact staged packet `/root/b60-operational-20261101-v1/packet.tar` SHA-256:
`41abce2639d62fd2244ff97b2b8e7f3cc2f7be46513c2c4534c26c27e08d7230`.
All archive members were checked for bounded regular-file/directory paths;
17 tooling modules and30 candidate modules were rehashed under root custody.
GNU tar ignored Apple provenance extended-header metadata; no source bytes,
dependency set or custody checks were relaxed. Tool descriptor SHA-256
`a2b1b0842f9d2e2dfe6afb96e2364dd3f81c7f0ac09cce91ef739c1eb9df2935`;
candidate descriptor `5e53c5242d027d2fb854f27d3a007242e34abcd6d0b5a4bf65385b73303251a0`.
Host adapter SHA-256 `cbfd43e00363e3fc9938e013691544da174d5fc0553b4530218aff77f34e26df`.
The portable source patch is
`scripts/b60-inference/source-update-host-20261101/0001-Add-guarded-root-source-update-adapter-and-real-file.patch`,
SHA-256 `ba44d6845b8203ccf71c49ac1f697a86032a4cbc7a2d5be109ae1bc4ab91b2b9`;
apply after `5c8453192` and its exact recorded dependencies.

The real guarded update returned `installed-not-activated`. It replaced only
`lab_hours_exclusive_admission.py` and `lab_hours_exclusive_cli.py` with the
already-reviewed diagnostic versions. All28 other runtime modules and all
guest helper code remain identical. No model/runtime service configuration,
historical activation profile, reservation or old evidence was overwritten.

| Proxmox source-update receipt | SHA-256 |
|---|---|
| `/var/lib/local-ai-lab/source-updates/diagnostics-20261101-v1/journal/update.json` | `d27ecfb472959aad27f1d7f59131c5351b7946b20f9b2384e4d854b6de89d898` |
| `/var/lib/local-ai-lab/source-updates/diagnostics-20261101-v1/files/manifest.json` | `396a1df5323ed348354f1b63a5e5a361977b9eaf9520411448324bbacd513b3d` |

Old public controller bytes/uid/gid/modes remain in that root-private checkpoint.
Rollback uses the retained staged adapter with `rollback` and the same exact
bundle hashes/attempt identity. Its guard now correctly refuses source changes
because future timers are armed. Any rollback must first reconcile those
timers and active owner; never bypass the guard or alter a running guardian.

## Next qualification independently verified armed

Used the existing `b60-exclusive-20261101` capacity record, not a new booking
or replay. Record SHA-256 remains
`55ed0e33edf8c1db637cf6cc357d2250af2599aabb4f3b4fb4b0d898a3116d4f`;
start1793527800/end1793530500, owner b60-stream-a, reserved/unclaimed. The
reviewed installer prepared five guest-local **metadata-only** plans and one
protected no-model profile. The reviewed dated scheduler then installed four
new unit files and started only their future timer clocks.

| Unit | Verified state | Next Vancouver time / epoch | Last trigger |
|---|---|---|---|
| `b60-exclusive-integrity-20261101.timer` | enabled, active/waiting | November1 01:15 UTC−07 /1793520900 | empty |
| `b60-exclusive-qualification-20261101.timer` | enabled, active/waiting | November1 03:10 UTC−07 /1793527800 | empty |

Both services: static, inactive/dead, MainPID0, no start timestamp. No November1
session exists. No lease/drain/operation markers or shared-directory flock
holders remained after preparation. The raw systemd display uses PDT for01:15
and MST for03:10 under its timezone abbreviation rules; exact epoch validation
confirms both are the intended Vancouver UTC−07 instants, not a shifted run.

Exact new file receipts on Proxmox:

| Path | SHA-256 |
|---|---|
| `/var/lib/local-ai-lab/exclusive-activations/b60-exclusive-20261101.json` | `1881b764b7dedadfaf60a5311e1dc04110d5547bfcb3f3e2d27fcc06d491022e` |
| `/etc/systemd/system/b60-exclusive-integrity-20261101.timer` | `518ccf90d4deedee8cce97ecfb4ab68f316ec4bb1545c3c6e8602cf5b8fbb244` |
| `/etc/systemd/system/b60-exclusive-integrity-20261101.service` | `d77001ae448ff397ffee2248833be27878ce302fa6552bb84828806de50130e5` |
| `/etc/systemd/system/b60-exclusive-qualification-20261101.timer` | `f822a3d8ed8e9279e7fe1822b9d8f0d26c6fc268b0cea05902efb372e1b2a4f2` |
| `/etc/systemd/system/b60-exclusive-qualification-20261101.service` | `55ea8b078a029daa0c2acb95a3df99ab077ba2024b5b6e08819b107ae956c5a6` |

All30 actual runtime hashes match the new profile; canonical pin-map SHA-256
`c9fbbd2039b1dabe0771a2b27128147df1be860ce88a2bf4317b4c504f17d739`.
All five actual plan hashes match the profile and equal the prior metadata
identities in [October31 arming](qualification-armed-20261031.md). An independent
show-only capture of all13 exact declared units also passed, including active
static narration. That is current observation, not proof no unit can become
unstable at03:10. The new diagnostics preserve the specific refusal if it does.

## Scope of tonight and durable next action

01:15 verifies same-cycle backups/first pull and archive integrity, bounded
through01:40. At03:10 the independent Proxmox owner must re-prove the complete
backup/pull/exact-mirror chain, source/resource/hardware/authentication and
consumer/trigger gates, capture actual entry, arm the independent guardian,
claim the common booking and perform **restore-only/no model** qualification.
Trial cutoff03:15; restore deadline03:55; buffer04:10;04:15 stays protected.

This work does not execute run/launch, stop AI services, mount model storage,
acquire an experiment lease or invoke a model now. Future arming is not a
promise that fresh admission or restoration succeeds. Next inspect sanitized
November1 integrity/session/entry/ledger/release and owner/guardian receipts,
restored service/schedule identities and actual lock release. Never export
guest recovery bytes, duplicate the owner, replay an expired booking or retry
device failure. Normal live recovery, independent owner-loss and reviewed
candidate/mount/resource recovery still precede35B experiments. Programme
remains active; this requested adapter/clock/arming milestone is complete.

Authoritative four peer refs were refreshed before operational work and remain
unchanged from [the preceding receipt](source-update-pending-20261031.md), with
B60 received `54e58d425c6032da0b5a05a1e7337bef9c91f72e`. Source publication is
liaison-only under standing authority; verify Forgejo and automatic GitHub
protection refs read-only. Publication does not imply peer reading.
