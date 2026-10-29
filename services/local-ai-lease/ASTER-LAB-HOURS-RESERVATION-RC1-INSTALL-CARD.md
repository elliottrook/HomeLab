# Aster Lab Hours reservation RC1 — install and qualification card

This card upgrades the passed RC1c transaction into the LH4 reservation-driven
service and adds the LH5 Doctor boundary. It changes no model, backend,
credential, firewall or backup schedule and performs no reboot.

## Install

Checkpoint all replaced paths. Install the five Python entry points, release
manifest and four systemd units from this commit as root-owned regular files;
Python and wrapper entry points are mode `0755`, JSON and units are `0644`.
Install `/usr/local/sbin/aster-lab-hours` as a fixed link or copy of
`lab_hours_booking_cli.py`. Run Python imports, the focused tests and
`systemd-analyze verify` from a temporary Linux staging directory before
touching installed paths.

Create `/var/lib/local-ai-lab/reservations/records` root:root mode `0700`.
Enable only `aster-lab-hours-dispatch.timer` and
`aster-lab-hours-doctor.timer`. The dispatcher service is inert without a due
booking.

## Qualification gates

1. Doctor is healthy while idle and the dispatcher reports `due=0`.
2. Overlapping and unregistered bookings fail without effects.
3. Two non-overlapping booked, scheduled smoke transactions each produce
   exactly three requests, restore production and reach terminal `complete`.
4. A controlled owner-loss exercise proves the separately armed guardian
   fences the exact owner, restores production and clears the shared state.
5. Final Doctor is healthy, reports the last booked success, and finds no
   owner, guardian, lab listener/process, lease, state or lock.

The first failed gate stops qualification. Preserve records and evidence.
Rollback does not delete them.
