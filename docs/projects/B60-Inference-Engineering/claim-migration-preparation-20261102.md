# Claim-window correction — exact offline migration preparation

Preparation-only continuation. The November1 pre-claim NO-GO is unchanged;
this work does not deploy a fix, claim a lease or arm a future job. No model,
GPU, benchmark, mount, service/timer, clock, package or credential effects ran.

## Exact transition, not a general source-write grant

Built and pinned the30-file runtime closure containing the tested claim-window
correction from [November1 reconciliation](qualification-no-go-20261101.md).
Compared it with the installed diagnostic baseline: exactly three modules
change. All27 other runtime files and all guest helper sources remain equal.

| Module | Expected installed SHA-256 | Candidate SHA-256 |
|---|---|---|
| `lab_hours_exclusive_boundary.py` | `7a8bda4fb724c6ed71925a4ebfe27578950971a08ffbd49085979a6f014556a0` | `5d4b7d53da18dcef6b7f1cc54c10cee5977bea3faa9f0626e5e1aa3cd78b54aa` |
| `lab_hours_proxmox_adapter.py` | `e44cc1a5be4f682d78135efb5a21c975d56cab9ae15af4596f21d6574795adc6` | `98e6e3c103ba0f780b0224d93661fb315adaba2e70c4c2ab8c1e0fc013ee1fd4` |
| `lab_hours_reservations.py` | `803a5dd1fddee2927248d4a67492ee24735f450bd3203f6e28f6d748b226a43c` | `7c0995f8eb96c83a37f6b5fe13b9118387f89fa26b290398bd9e59ad3e46dfdd` |

Local candidate `/private/tmp/b60-claim-candidate-20261102-v1` descriptor
SHA-256 `11c1456e52463a5fafc8675ab71a966ba7f9450faf36177cc67775c54fde9f57`;
canonical pin-map SHA-256
`e16b3bfe02f8a12e08271b6e95baddf206192cbd37e765d0d9c5dee929608b82`.
The expected old bundle is the protected existing Proxmox packet at
`/root/b60-operational-20261101-v1/payload/candidate`, descriptor
`5e53c5242d027d2fb854f27d3a007242e34abcd6d0b5a4bf65385b73303251a0`,
pin-map `c9fbbd2039b1dabe0771a2b27128147df1be860ce88a2bf4317b4c504f17d739`.
An operational continuation must re-prove actual target bytes; this is not a
claim that merely naming an old packet authenticates current production.

## Migration adapter prepared and tested

Source `34ff36fbe39cfae9f12da5bf03b757a2c8859edb` adds one exact transition
policy to the existing guarded updater. It does not replace its old policy:
the former v4→diagnostics two-module path remains separately pinned. The new
path accepts only the complete c9→e16 maps, the three names above, and attempt
identity `claim-window-20261102-v1`. Skipping from v4 directly to e16 or using
an unlisted reverse/altered map refuses. Rollback still uses the original
verified transaction/checkpoint, not a newly authorized reverse installation.

Checkpoint inventory, per-file effect scope, row count, atomic replacement
and recovery all derive from that exact matched policy. No caller may supply
arbitrary filenames or a broader mutation inventory. Existing shared exclusion,
active owner/guardian/session/claim refusal, future-timer refusal, root custody,
old-byte comparison and import verification remain mandatory.

Added the complete five real-disposable-file tests for the three-module path,
including actual child exit after each of its three atomic replacements,
round-trip rollback/modes, candidate corruption, import failure and foreign
source rejection. Added a policy test for exact scope/identity and skipped /
reverse baseline rejection. These are local disposable effects with fake
host-idle proof, not a production deployment or live restoration qualification.

177 Lab Hours tests,10 installer tests and115 focused B60 tests pass without
skips against the exact independent replay. Equal source/replay tree:
`e0ad96cea74ad4990c93a40ca3b24c10f563a06e`.
Portable patch after the existing claim-window correction `df09a99e2`:
`scripts/b60-inference/claim-migration-20261102/0001-Pin-the-claim-window-source-migration-with-exact-thr.patch`,
SHA-256 `4b3450410d47677f2d935d5b7836b9977c8e7d218fe562bcd790ff509a966c6a`.
Core SHA-256 `fbda1950d89df24155b76beb609d24e152ac0a84ed369271a9826bed4d88b1d5`;
host adapter `27beec2730b379b80da66b3db9309e7716c82bed0b5944afbed8e9df10f0dcec`.
The tooling import closure is built locally at
`/private/tmp/b60-claim-migration-tools-20261102-v1`,17 modules, descriptor
SHA-256 `1b435fdc48a94d8305b168c5ae39cddf57dcc12113a3a15549793eb03e1f6d03`;
nothing was uploaded.

## Actual next booking receipt and operational continuation

At host epoch1793577640 the minimal control-plane probe found no known
lease/drain/operation markers or common-directory flock holders. It then read
only the next reservation metadata:
`/var/lib/local-ai-lab/reservations/records/b60-exclusive-20261102.json`,
SHA-256 `87da8328e620a748caa67b5c4f637f7921ae93393f4d3f7b237ad71dc3c2188a`.
Owner b60-stream-a, reserved/exclusive-stack; start1793614200/end1793616900,
03:10–03:55 Vancouver UTC−07,900-second buffer. Its activation path is absent.
**Capacity is reserved; a future qualification is not armed by this work.**

Next operational continuation, under existing Stream A authority but outside
the restrictive preparation heartbeat:

1. Recheck actual time/booking, shared-owner release, backup clock and source
   identities. Never assume a prior release observation remains current.
2. Stage only the pinned tool/candidate closures under fresh root custody;
   verify descriptors/all files and rerun the disposable target tests using
   all three exact old/diagnostic/claim fixture bundles. Do not fetch models.
3. Run the guarded source updater with expected c9 old bundle, e16 new bundle
   and fresh `/var/lib/local-ai-lab/source-updates/claim-window-20261102-v1`.
   No AI service/model effect occurs in that source transaction. Require the
   protected checkpoint and exact complete import/pin proof; on uncertainty
   retain evidence and use its bounded rollback, never overwrite foreign work.
4. Only afterward prepare five new guest metadata plans/no-model profile for
   the still-future booking and run the reviewed date-specific scheduler.
   Verify enabled/waiting01:15 and03:10 clocks, exact epochs/source/profile /
   plan pins, no last triggers and inactive services before reporting armed.
5. The independent runner alone performs future restore-only qualification
   after same-night backup/mirror/resource/consumer gates. Keep original
   trial/restore deadlines and04:15 protection. No expired replay, model trial
   or automatic device retry. Next reconcile actual receipts, not launch status.

If the booking ceases to be future, do not reuse it or substitute dates without
fresh source-bound planning. No new human model permission is missing. This
record supplies preparation, not background execution, deployment or success.
Normal recovery and independent owner-loss/candidate-resource proof remain
before27B+ reasoning-on model work; Adaptive still owns capability/policy bars.

## Exact peer receipt refresh

Fetched/read BOTH liaison branches plus registry/owning booking branch. No new
peer reply. The complete commit/path/hash receipts remain those in
[November1 reconciliation](qualification-no-go-20261101.md): Adaptive
`d88f8239b6771836c3e56c59229db81a8c18ddd6`, registry
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`, booking owner
`5a9c3471398cfeecc0c6db35bfb264f87d8318f9`, received B60
`b29df19f949052f23aef26efe47e838958ef9dd0` with arming-record SHA-256
`e3d2ab5a4eb374a7969786ea4674cf92e162f2f92e9e39cbac4f004aff3307f8`.
Publishing this meaningful new source/evidence liaison packet does not imply
peer reading or authorization for any broader remote change. Only the standing
coordination branch may be pushed; GitHub protection is verified read-only.
