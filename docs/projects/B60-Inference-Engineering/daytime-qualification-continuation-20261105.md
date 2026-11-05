# November5 daytime qualification — operational continuation

**Migration and arming COMPLETED. Do not replay the steps below.**
Read [the verified arming record](daytime-qualification-armed-20261105.md) first.
At12:40 reconcile actual scheduled receipts and restoration; existing steps
below document the implementation history. Root arming receipt SHA-256
9b559af510ca192a37c12f11c6b9087d63e4aa4fb0a19bde501b3c7ec2ddfdfd.


Jason explicitly instructed “so qualify before tonight ... Continue”. This is
operational Stream A continuation, not the restrictive preparation heartbeat.
Do the guarded migration, fresh plan/profile preparation, arm and reconcile the
actual restore-only transaction. No further conversational approval is missing.
Never call a fake test qualification; no large-model experiment follows yet.

## Real reservation and current external owner

Created `b60-exclusive-20261105-day-r1` in authoritative ledger, exclusive-stack,
b60-stream-a, start1793907000/end1793909700: November5 **12:30–13:15 UTC−07**,
plus900s recovery buffer through13:30. New, once-only ID; no prior attempt reused.
Current known peer `aster-stream-a-sa3-candidate-j-quality-20261105-1016-r1`
has start1793898960/end1793902560 (10:16–11:16) plus reserve. Do not assume
release from a deadline. Query minimal `/usr/local/sbin/local-ai-lease status`
and marker existence first. If active/uncertain, do not upload, migrate or probe
the stack; wait/recheck actual release. Never bypass/delete another owner.

Two added104 paths identified metadata-only: `/etc/aster/asterremote.env` and
`/etc/systemd/system/aster-agent.service.d/zz-asterremote.conf`. They are within
existing declared roots. Contents remain source-local; no credential export.
Fresh plans must be generated for all five guests under the new booking ID.
Old November5 plans and failure receipts remain immutable.

## Reviewed source / packet

Source checkout `/private/tmp/b60-resource-checkpoint-20261104`, commit
`37a80b60444221cf6c87bafaf7214fa176b96dad`. 194 controller tests, five daytime tests
and115 B60 tests pass. Original c9 test fixture had disappeared; reconstructed
in NEW `/private/tmp/b60-reconstructed-c9-fixture-20261105` from exact v4 and
pinned claim files, verified canonical c9 map. Original directory untouched.
The first all-suite attempt failed only because that fixture was absent; full
rerun passes after exact reconstruction. No production acceptance inferred.

New runtime bundle `/private/tmp/b60-daytime-candidate-20261105-v3` descriptor
SHA-256 `668bb423235e02118f83460d9fe004560ae27d1eb148fc3c294e2334a616c9cc`.
Exact30-file map old20e2→new
`09597ea2edd6c6e0b24b7036f8974b69c6cf3617d0a159fe937de89934a3675d`.
Only admission, plan identity helper, Proxmox adapter and unit inventory change. The active calendar EPUB monitor timer/service are included, giving15 consumer rows. Admission retains night restoration
buffer before04:15; separately booked daytime restore-only work starts≥06:30,
finishes with900s reserve≤22:00, same date and≤90minutes. Same-day backup,
whole-job, exact mirror, fresh integrity, source, resource, consumer and shared
exclusion checks remain required. Guest endpoint errors now retain only reviewed
fixed codes with guest/action; arbitrary exception/config/argv text is rejected.
The plan identity helper must also migrate in all five guests; its existing nightly IDs remain valid and distinct -day-rN IDs are newly allowed.

Packet `/private/tmp/b60-daytime-operational-20261105-v3/packet.tar`, SHA-256
`3178dffff8faf4519e7cc08213d9b8631eb2f895bdcf7e0824e2bcb3ca694ebd`.
Contains candidate and41-module tooling closure. `tool-pins.json` SHA-256
`9d071b7266070d61c830aefb566938902ce462632d590490eab765a4b7fb6336`.
Tar ownership root/root, dirs0700/files0600. Stage only after actual owner
release in NEW `/root/b60-daytime-operational-20261105-v3`; refuse preexisting
unknown stage, verify archive before extraction and every candidate/tool hash.

Old root-private bundle already retained:
`/root/b60-resource-operational-20261104-v1/payload/candidate`, descriptor
`d58e4c9e5f04e68319696a9eb5a27dc8212327c31ec5c7ff083337708afb4f18`.
Verify exact old30 source map against installed exclusive-session before effect.
Do not copy credentials or old recovery configuration out of their source.

## Ordered actual operations after release

1. Stage/hash-check new packet as above. Run target Linux disposable tests from
   payload/tools. Import `test_lab_hours_source_update_host` and set
   `DaytimeHostAdapterTests.old_bundle` to the retained old root bundle and
   `.new_bundle` to staged candidate; load ONLY that class, plus AdmissionTests
   in test_lab_hours_exclusive_admission, GuestFailureDiagnosticsTests in
   test_lab_hours_proxmox_adapter and DaytimeQualificationTests in
   test_b60_daytime_qualification. No default historical fixture substitution.
   Target testing uses disposable paths and fake idle evidence, not live proof.
2. From payload/tools run reviewed `lab_hours_source_update_host.py apply`
   with --old-bundle retained old path, --old-sha256 d58e..., --new-bundle staged
   candidate, --new-sha256668bb4..., --attempt
   `/var/lib/local-ai-lab/source-updates/daytime-qualification-20261105-v1`.
   Exact transition policy is in staged tooling. It holds shared exclusion,
   idle/known-pin/custody guards, preserves source checkpoint, validates all30
   imports and rolls back recognized bytes on failure. Do not use an ad hoc
   overwrite or stage optional unrelated diagnostics.
3. Migrate ONLY `lab_hours_unit_adapter.py` and `lab_hours_prepare_entry_plan.py` in all five guests using
   staged `lab_hours_daytime_plan_helper_update.py`, hash
   2aca4ecb1477e7eef98f6e6d24aa6bebd866bcb7d242331827b1460e281de35e.
   Host caller MUST hold shared `host_exclusion(ROOT)` and check idle throughout.
   Target old helper be5637c7974c34d8da121830be575ea2695a8e5862e39f7b54c6b89b8b5c1c5b;
   new2cf80b75ca067c2d9bb2aad861c81261ed304177e24040dff8f33487c883778a.
   Stage exact updater + candidate plan helper + unchanged lab_hours_file_checkpoint.py
   in each guest NEW `/root/b60-daytime-plan-helper-20261105-v1`, root0700/0600.
   Updater compares exact old/new, checkpoints source, imports target and rolls
   back on import failure; retains guest-local source-updates/daytime-plan-identity-20261105-v1.
   Run four disposable GuestHelperTargetTests from test_daytime_plan_helper_update_target
   first, with B60_TARGET_FIXTURE_ROOT root-private and B60_DAYTIME_OLD_SOURCE_BUNDLE
   /B60_DAYTIME_NEW_SOURCE_BUNDLE set to exact old/new root bundles.
   No guest config or service change is part of helper migration.
4. Run staged `install_lab_hours_exclusive_dormant.py` --source staged candidate
   --manifest-sha256668bb4... --booking-id b60-exclusive-20261105-day-r1
   --install-dormant (confirm exact parser flags before invoking). It must
   preserve every installed source and prepare all five current metadata plans
   plus protected qualification-only profile, experiment null/trial300. Check
   all source/plan/helper hashes, no secret bytes transported.
5. Run staged `install_b60_daytime_qualification.py` --booking-id same ID
   --preparation-source staged tools/b60_daytime_integrity_prepare.py
   --preparation-sha256
   da306284f640b74585b67af8e976d5181d95a2d5caae240c290b12fbff448001
   --schedule-qualification. Scheduler hash
   `2e605f051a9682856d6b5d59854d972781d95e04e84ebee4782b5b050f46e1c7`.
   Its unique booking-specific units avoid today's spent nightly units.
   It refuses if integrity start is less than120s away. Desired next times
   November5 **11:35 integrity** and **12:30 qualification**, date-specific,
   nonpersistent, empty prior triggers/inactive services. Do not manually invoke
   stack run or integrity effect now or replay expired schedule. If timing gates
   become stale, retain reservation/evidence and select a fresh clear future
   daytime booking with sufficient preparation time; do not relax gates.
6. Independently verify actual next dates/enabled/active/waiting/empty previous
   triggers, inactive services and full profile/30-source/five-plan hashes.
   Only then call armed. Retain sanitized root-private arming receipt plus hash.
7. Integrity producer runs independently at11:35, verifies existing same-cycle
   backup and first TrueNAS pull, reuses only a≤3h valid receipt or performs a
   fresh bounded low-priority archive scan; saves previous receipt root-local.
   It does not stop the stack, mount storage or alter backups. Capture bound
   is25min/available40min; model admission still independently verifies all pulls.
8. At12:30 independent host owner captures entry, arms guardian, claims once,
   drains/restores exactly entry; no experiment/model switch. Read resulting
   source-bound integrity/admission/session/terminal receipts after completion.
   Check actual production restoration, timers with no missed-job replay and
   shared release, not just launcher exit. Failed/uncertain is terminal; no GPU
   retry or duplicate lease. Further recovery qualification remains separate.

Publish sanitized meaningful receipts/questions ONLY to
codex/b60-adaptive-coordination under standing authorization, verify automatic
GitHub mirror read-only. Never main/force/delete/workflows/GitHub direct push.
Retain focused local commits. No backup/schedule/driver/boot/credential changes
outside these new qualification units. Preserve TTS and all unrelated work.

## Updated peer interpretation

Owning platform e93270d58f0bf7948ae7097fdda946fd2fd49c35 and Adaptive77bb10d5be5f71b822690666611101f2f3c8aaeb supersede the stale EPUB postcheck: legacy host scheduler must remain disabled/inactive, guest monitor enabled/active, retired worker timer disabled/inactive and worker inactive/success between registered jobs. R3 public gate is eligible for untouched evaluation, not a quality or routing grant. Do not enable the retired host scheduler. Read-only preflight must reconcile current timer metadata/consumer coverage before any isolation; never stop an independent monitor merely because its name is new. Current peer quality booking is a separate owner and must actually release.

## Actual progress / remaining work

Actual peer release established at1793899314: authoritative peer booking complete, finished1793899192, shared markers absent. Current five-plan metadata differs only in the two declared104 additions. EPUB worker timer is retained disabled/inactive with monotonic triggers; active monitor timer is calendar03:30, Persistent=yes and triggers monitor.service. Include that timer/service in checkpoint/drain/no-catch-up recovery; do not revive retired worker timer.

New v3 source packet verified on target,30 runtime/41 tool pins, root custody.31 target-Linux disposable tests passed. Exact four-module guarded migration returned installed-not-activated. Guest unit and plan helper migrations then started under continuous shared exclusion and idle checks, with each root-private source checkpoint retained. Do NOT repeat already-completed migration or replay a completed helper. Inspect actual pins/checkpoint receipts first. Next fresh five plans/profile, scheduler installation, independent arming receipt and actual12:30 terminal reconciliation. This paragraph is not an arming/qualification claim.

Unit helper updater hash536ba72ad79b3ff59df0f415496249ed305a529ef576f7f2f2213c90c3b7e81d; old unit helper37380e4fcc9f38c3927cc42f3a7e1934a58ba3faccc414f034c707468816adf4→newe7869856219ba14ca1b8d4db5fd29654b48666eef4d21e26b77772d13805312f. Stage in each guest /root/b60-daytime-unit-helper-20261105-v1 with updater, exact new helper and unchanged file-checkpoint module. Guest checkpoint source-updates/daytime-unit-inventory-20261105-v1. Existing plan helper procedure above is second.
