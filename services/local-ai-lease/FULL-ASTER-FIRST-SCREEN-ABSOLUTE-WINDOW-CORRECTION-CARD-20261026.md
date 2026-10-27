# Full-Aster first-screen absolute-window correction — October 26

Status: **SOURCE CANDIDATE / LIVE INSTALL AND SCHEDULED EFFECT NOT AUTHORIZED BY THIS CARD**

## Finding

B60's exact peer characterization correctly showed that the public
non-authoritative preflight accepts caller assertions without proving current
time. That helper is not imported by the installed effect controller. The live
controller instead reads the fixed F2/F3 sources, produces F4/F5 itself, binds
their bytes to one generated full-drain lease, and requires the independent
guardian before the owner scope.

Review of the actual launcher found one separate live gap. Its guardian used
30- and 45-minute deadlines relative to process start, while the approval card
allowed a start only from 03:10 through 03:30 Vancouver and required completion
by 04:15. A delayed service start after 03:30 was not rejected and could move
the hard deadline beyond 04:15.

## Correction

`full_aster_first_screen_launch.py` now accepts only October 27, 2026 from
03:10:00 through 03:30:59 America/Vancouver. It keeps the 30-minute effect
limit, requires a real 15-minute recovery interval, and caps the guardian hard
deadline at 04:15. An invocation outside the date/window exits before the
guardian, owner, lease, service stop, mount or model request.

This changes only the launcher source. The installed launcher and transient
03:10 timer remain unchanged until a separate reviewed installation replaces
the exact file. The already approved effect must not run with a different
source hash unless that replacement is explicitly accepted.
