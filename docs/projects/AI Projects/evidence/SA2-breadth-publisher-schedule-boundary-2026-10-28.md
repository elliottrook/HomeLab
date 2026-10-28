# SA2 breadth publisher schedule boundary — 2026-10-28

## Result

**SOURCE-ONLY PASS; INACTIVE.** The existing daily HomeLab report invocation
now requests the schema-3 catalogue output needed for `backup.protection`, and
an inactive five-minute systemd timer/service pair is defined for the sanitized
Aster Agent journal-count report.

## Existing Doctor schedule

`ca.yampy.homelab-report` already invokes the repository's
`scripts/scheduled-report.sh`. The source change adds one argument to that
existing builder call:

`--catalogue-output "$state_dir/diagnostic-catalogue.json"`

The builder still publishes the aggregate first and the digest-bound catalogue
last. A racing reader sees either a matching pair or safely abstains. No new
Mac schedule, LaunchAgent, collector run or publication occurred during this
work.

## New log publisher schedule

The inactive `aster-agent-log-report.service`:

- is a root one-shot with no environment or credential file;
- invokes only the fixed sanitized publisher;
- can write only `/var/lib/aster/source-reports`;
- permits only `AF_UNIX`, uses a private temporary directory and applies
  systemd filesystem/memory hardening.

The inactive timer uses two minutes after boot, five minutes after each run,
30-second accuracy and no persistence. It does not stop, restart or call Aster
Agent. Neither unit is installed or enabled.

## Validation

Shell syntax and the complete focused publisher/evidence suite pass **84/84**.
The fixed report producer and unprivileged consumer already passed a temporary
target compatibility check; the remaining gate is exact release packaging,
disabled target unit validation and approval for installation/enablement.
