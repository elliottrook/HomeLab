# Fresh October 31 activation — prepared, awaiting actual host release

Jason explicitly instructed this chat to proceed Stream A after being told
that no new qualification was armed. This is an operational continuation,
not a preparation-only heartbeat. No repeated user approval is missing.

## Exact progress

- Existing future `b60-exclusive-20261031` remains reserved, owner b60-stream-a,
  kind exclusive-stack, start `1793441400`, end `1793444100` (03:10–03:55
  Vancouver October31). Booking file SHA-256
  `9ca18763b854ec6800a9431dafae9c26a3bec381955f0fc38ff636ed7fe34d1f`.
- New activation/session/October31 timers and dated prep directory were absent
  at preflight. No need to book again or reuse October30.
- Verified installed30-file closure through protected October30 profile.
  Canonical pin-dictionary hash remains
  `f5085fbb7b7e8e456be6ac6157867a1af8e808a2e139fb64c03caeb991d25e85`.
  Keep the optional diagnostics update undeployed for this qualification.
- Staged an exact copy of this already installed source under
  `/root/b60-exclusive-20261031/source` on Proxmox, root-private. Descriptor
  SHA-256 `ce2ed7f7165160277eb627e496077adfd8c8fe6d476b62a2d888429f76d10ab4`.
- Called the exact retained dormant installer; it refused at shared directory
  flock acquisition, **before target/guest/profile effects**. The new stage is
  preserved; do not recreate it or delete another owner's locks.

## Real concurrent owner

While the earlier helper reported ready, another operation acquired the
authoritative host directory flock. Observation at epoch `1793383473`:

- holder PID3724427, cgroup
  `aster-local-ai-pilot-owner-lh-d58933c47faba1532798.scope`;
- durable owner `lh-d58933c47faba1532798`, lease
  `lh-d58933c47faba1532798:1793383201`, phase drained;
- lab end `1793385961`, restore deadline `1793386861` (12:01:01 Vancouver);
- full-inference drain metadata/lock present, no manual-helper lease marker.

This is an actual live owner, not an approval wait. Do not probe guests, stop
the owner or bypass its flock. The deadline is not proof it restored. Require
real release and absence of active/uncertain maintenance before continuing.

## Scheduling correction, source-only so far

Implementation commit `56cd9c35c` makes the qualification scheduler use a
separate prep package per date rather than rejecting a second night because
the October29 shared prep directory exists. It never overwrites old files.

- New scheduler source SHA-256:
  `1a62e2da5217463b2f8dbce6362b8a8956ff1f18685f298898b69c869bcb0a64`.
- Unchanged dormant installer SHA-256:
  `90ab0ff837c7cc624f0710978b7e5ddbd16a7f973cadcd595aa885674973d16c`.
- Unchanged integrity producer SHA-256:
  `af8e054b2032c80f3d27f95bee0e603ef34aefa9cb05ce2f0c60c4460fd85c01`.
- Published patch under `scripts/b60-inference/next-qualification-20261031/`.
-130 offline Lab Hours tests pass in implementation and independent replay.
  Replay tree `a4d2f31b8dcccc1cc546f07bbae43cbaca3b8dda`. No live result.

## Exact operational continuation after the other owner releases

1. Read-only reconcile full-inference drain, common exclusion, lease, booking
   and current source identity. If any owner/claim/uncertain recovery remains,
   yield; never clear state or assume a deadline completed restoration.
2. Reuse protected `/root/b60-exclusive-20261031/source`. Verify its descriptor,
   pins and exact files; invoke existing reviewed installer at
   `/root/b60-exclusive-wiring-20261029.WsPURv/install_lab_hours_exclusive_dormant.py`
   for booking `b60-exclusive-20261031`. Its own shared exclusion/ready/time
   gates remain mandatory. It prepares current source-local metadata plans
   and a no-model profile; it must not overwrite changed controller code.
3. Stage only the reviewed new scheduler (from implementation checkout
   `/private/tmp/b60-exclusive-contract-20261029.y6kxwF/repo/scripts/local-ai/`)
   into the fresh root-private stage; verify its SHA above. Run it using the
   unchanged integrity producer at the old reviewed staging path, matching its
   SHA above. Use `--schedule-qualification` for the October31 booking only.
   It requires the booking at least two hours away and absent dated unit paths.
4. Independently verify October31 01:15 integrity and03:10 qualification timers
   enabled/active, exact next dates, no prior trigger, source/profile/guest-plan
   pins and service inactive/MainPID0. Static validate is not arming proof.
5. Persist sanitized exact path/hash/arming receipts; publish liaison only
   within standing authorization and verify automatic GitHub mirror read-only.

Do not load a model, drain services, mount storage, acquire an experiment lease
or invoke run/launch now. The scheduled Proxmox owner alone will act inside the
booking after fresh completed backup/mirror gates. Restore entry before03:55,
retain recovery buffer through04:10, preserve04:15 protection. Failure does not
authorize replay or automatic GPU retry. Report truthfully if not armed.
