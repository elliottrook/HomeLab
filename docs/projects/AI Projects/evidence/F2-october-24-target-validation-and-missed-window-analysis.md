# F2 October 24 target validation and missed-window analysis

**Validated:** 2026-10-23 04:00–04:10 America/Vancouver. **Activation state:**
inactive; no timer installed or enabled.

## October 24 target validation

Stream A exported the two candidates from platform commit
`054ada0698d4b35cf99217b1d6fe7bac97ff1cb3`, copied them only to Proxmox
`/tmp`, and removed them after testing.

- Candidate hashes matched the reviewed card:
  `0b13bcd…53376` prepare and `81c7cb6a…a666860` final.
- `systemd-analyze verify` accepted both timer files.
- `systemd-analyze calendar` normalized the events to October 24 at 01:15 and
  01:20 PDT (08:15 and 08:20 UTC).
- The installed coordinator and four supporting sources matched all five
  reviewed SHA-256 pins and were root:root mode 0644.
- Recurring F2 timers were disabled/inactive; the October 24 cycle state,
  cooperative lease state/lock and trusted receipt were absent.
- LXC104, LXC110 and LXC116 were running; `pvescheduler` and `pvestatd` were
  active.

This validates readiness for an activation decision. It does not prove the
future 00:30 backup or 01:00 TrueNAS completion and does not activate F2.

## Why October 23 was missed

The candidate was prepared and independently reviewed by 08:02 PDT on October
22, about seventeen hours before its first timer. The technical packet was
ready. The distinct host-activation approval was not received before 01:15,
and the timers correctly remained absent. The miss was therefore an approval-
workflow failure rather than a backup, GPU, timer, or F2-code failure.

The process also made the miss easier: the activation request was carried in
periodic progress notifications while offline work continued, rather than
being raised once as a clearly timed blocking decision soon after the review.
There was no authorized recurring host timer to compensate. Near-midnight
reminders could not create permission, and the fixed cycle then expired.

## Corrected cadence

For future exact-cycle work:

1. Finish and independently review the dated card before 12:00 on the prior
   day where possible.
2. Immediately present one exact activation request with the decision deadline
   and effects; do not bury it in a general progress report.
3. If still unanswered at 18:00, send one action-required reminder. Continue
   offline work, but keep the pending gate explicit.
4. If approval is absent by 22:00, mark that cycle unavailable and prepare a
   fresh later date. Never rely on a final-hour request.
5. After approval, validate and install the inactive exact-date units during
   the day, plus the observation-only cleanup schedule. The timers themselves
   wait for the backup-cycle gates.

This cadence does not weaken the per-cycle activation gate or infer approval
from a clock.
