# LXC110 mirror schedule corrected — October 30

Jason explicitly requested analysis of the schedules and moving the 04:20
mirror outside Lab Hours. Changed only TrueNAS rsync task 3 to **02:00 daily**.
It remains enabled. No immediate mirror, benchmark, service drain, lease or
qualification retry was started.

## Selection and live validation

Observed Proxmox all-guest backup: 00:30. TrueNAS task 1 guest pull: 01:00
(latest duration 7m28s); task 2 Mac pull: 03:00 (latest duration 1s).
Task 3's latest mirror took 6m20s. These are observations, not guaranteed caps.
B60's 30 capacity reservations are 03:10–03:55, with restoration protection
through 04:10; 04:15–06:15 remains protected analysis and 06:15 the digest.

02:00 is before the booked exclusive work, after the normal guest pull and
before the Mac pull. It matches the existing fixed admission contract, so
no admission code or source pins need changing. Runtime admission still
requires actual completed non-overlapping jobs and exact same-cycle mirror
evidence; a schedule alone never establishes this.

Also inspected TrueNAS snapshot/replication and cron schedule metadata. There
are no replication tasks or other inspected job starts at 02:00. Unrelated
media work starts at 01:30 and other storage jobs at 04:30 or later; their
duration/isolation is not certified by this narrow change. Those tasks were
not changed, and no general whole-host contention guarantee is claimed.

TrueNAS timezone is `America/Los_Angeles`, not Vancouver. Today both show the
same Pacific clock, and 02:00 matches the admission contract's expected local
hour. Timezone was not changed. Future offset changes remain a fresh-gate
concern, not permission to shift reservations silently.

## Transaction and receipts

The first supported API update returned an error; immediate read-back proved
task 3 remained at 04:20. Its exact error detail was not retained, so do not
invent a cause. Installed `rsync.py` shows update defaults to transient remote
path revalidation and host-key enrollment off. For this schedule-only change
to an unchanged, already working source/destination, the successful update used
`schedule={hour:2,minute:0,dom:*,month:*,dow:*}`, transient
`validate_rpath=false`, and `ssh_keyscan=false`. Those flags are removed before
storage by the installed validator. They do not relax runtime SSH authentication
or known-host verification. No key or credential was read, changed or copied.

Compared all three tasks before/after using an allowlisted configuration
projection (source/destination, schedule, enabled state and rsync options):
only task 3's schedule changed. Canonical sorted JSON projection SHA-256:

- before: `5fcf21232129998e8dc824e57a9d768a4ce183acde18ffea8170a3b4f803bb63`
- after: `4795c831c0068a909d9908ebbc0ab5c4d28186e18f0e36f2e28afb052d3fe880`

Independent read-back via Proxmox's existing fixed TrueNAS observer confirms
enabled tasks 1/3/2 at 01:00/02:00/03:00. Three offline mirror-schedule
regressions pass, including the expected-chain positive control. No future
backup success or live restoration is inferred from this update.

Rollback, only if needed and after conflict review: update task 3's schedule
back to 04:20 using the supported API; this restores the previous conflict
and must leave lab admission closed. Do not change other task fields.

## Next action

The schedule conflict is resolved. The failed October 30 booking and receipts
remain untouched. Prepare a fresh future qualification activation with reviewed
pins and same-cycle backup gates; do not replay the expired booking. Remaining
bookings are capacity only, not automatically armed experiments. Actual normal
restoration, owner-loss and candidate/mount/resource gates still precede 35B.
