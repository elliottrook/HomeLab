# B60 exclusive Lab Hours — first qualification operator note

The30 capacity bookings October30–November28 are real,03:10–03:55 local,
with the existing15-minute reservation buffer. They do not mean30 automatic
experiments. Only the first restore-only qualification is currently activated.

## What is scheduled tonight

October30 America/Vancouver:

- 01:15: low-priority, bounded verification of existing same-night backup
archives. It changes no AI service and must finish by01:40. Known maintenance,
busy backup IO, failed source checks or stale/unexpected receipts stop it.
- 03:10: inside `b60-exclusive-20261030`, the Proxmox owner verifies fresh
admission, captures the actual entry configuration in protected local custody,
arms a separate Proxmox guardian, claims the booking, drains the declared AI
stack, then restores/verifies/releases. No candidate model is loaded or scored.
- 03:15: trial cutoff; the independent guardian fences an unfinished/lost owner
and attempts recovery. The restoration deadline is03:55, earlier than the
external04:15 protection boundary.

Both clocks are non-persistent future one-shots, not missed-job replay. They
run on Proxmox independently of chat/Mini connectivity, but still require the
actual host and all source gates. For example, a failed fresh Mac backup pull
keeps admission closed; a clock firing is not a passing experiment.

## Read-only status

On Proxmox, inspect only the new job identities and bounded metadata:

```text
systemctl show b60-exclusive-integrity-20261030.timer b60-exclusive-qualification-20261030.timer --property=Id,ActiveState,UnitFileState,NextElapseUSecRealtime,LastTriggerUSec
systemctl show b60-exclusive-owner-b60-exclusive-20261030.service b60-exclusive-guardian-b60-exclusive-20261030.service --property=Id,ActiveState,MainPID,TasksCurrent
python3 -B /usr/local/libexec/local-ai-lease/exclusive-session/lab_hours_exclusive_cli.py validate --booking-id b60-exclusive-20261030
/usr/local/sbin/local-ai-lease status
```

`static-profile-valid` verifies protected profile/source custody and pins. It
explicitly does **not** report arming state; the timer observations above own
that fact. `ready` is lease availability, not successful stack qualification.

The preparation result is
`/var/lib/local-ai-lab/exclusive-integrity/b60-exclusive-20261030/terminal.json`.
The stack session state is
`/var/lib/local-ai-lab/exclusive-sessions/b60-exclusive-20261030/session.json`.
Also reconcile the root-owned authoritative reservation record. Success needs
the exact source/entry identities, restored schedules, released ownership and
honest trial outcome—not merely an exit code, inactive process or old success.

Do not export the guest directories
`/var/lib/local-ai-lab-entry/b60-exclusive-20261030/files`. They can contain
source-local protected configuration recovery bytes. Only approved sanitized
metadata/hashes leave their guest.

## Failure and recovery boundaries

Do not delete lease/state/operation markers, reuse a booking ID or launch a
second experiment. Before a claim, failure must have no AI effects. After a
claim, the existing independent guardian is the first recovery owner. Inspect
its exact identity and durable state, not another project or wildcard unit.

The explicit recovery entrypoint is:

```text
python3 -B /usr/local/libexec/local-ai-lease/exclusive-session/lab_hours_exclusive_cli.py recover --booking-id b60-exclusive-20261030
```

This is an **effectful administrative recovery**, not a status command: it
fences the exact owner, validates binding/custody, stops only the declared
stack, and restores entry. The agent must first reconcile actual ownership
and the failed phase; do not race a healthy guardian. Unknown ownership,
source/mount drift or an unverifiable checkpoint remains fail-closed. Never
automatically retry a GPU/device failure. Restoration after a missed deadline
is emergency cleanup, never a passing qualification.

## What Jason needs to do

No additional general or per-model approval is required. No manual launch is
needed for these verified clocks. Separate exact risk authority remains needed
for excluded global driver/kernel/boot, credential, destructive or exposure
changes. The current model stays unchanged outside booked exclusive work.

After this qualification, actual owner-loss proof and the reviewed candidate /
mount/resource adapter still precede35B testing. The first35B milestone remains
reasoning-on grounded improvement at fresh9B p50 ANDp95 useful-answer latency;
none of tonight's controller work is a result against that bar.
