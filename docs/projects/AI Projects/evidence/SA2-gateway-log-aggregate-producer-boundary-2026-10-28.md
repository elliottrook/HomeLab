# SA2 gateway log aggregate producer boundary — 2026-10-28

## Result

**SOURCE-ONLY PASS; NOT DEPLOYED.** A fixed root publisher and unprivileged
Aster adapter now form a bounded log-evidence path. The model receives only a
count of priority 0–3 Aster Agent journal events in the previous 15 minutes.
Messages and arbitrary journal fields are never requested or published.

## Rejected first design and correction

The initial adapter attempted the fixed field-restricted journal query directly
from Aster. Target validation showed that production Aster runs as user/group
`aster` without journal membership, so the query exited `1` with no output.
Granting Aster journal access would have widened authority and risked exposing
unreviewed messages.

The corrected design keeps that denial in place:

1. a root publisher invokes one exact `journalctl` command for
   `aster-agent.service`, current boot, previous 15 minutes, priorities 0–3,
   maximum 200 rows;
2. `--output-fields` requests only priority and trusted journal metadata;
3. every returned JSON row must have the exact expected metadata fields and a
   valid priority/timestamp;
4. the publisher atomically writes a root-owned, Aster-group-readable mode
   `0640` report containing only count, fixed window, generation time and
   truncation flag;
5. Aster opens that fixed report without following links and exposes only the
   count, fixed window, service label and report digest.

Zero events maps to `ok`; one or more maps to `warn`, which means only that
high-priority events require review. Missing, stale, malformed, unsafe or
unreadable evidence becomes content-free `unavailable`.

## Validation

- The full publisher, backup, network, config, log, producer and proposal-path
  suite passes **81/81** locally.
- The service/publisher candidate passes **68/68** under LXC104's application
  Python and installed dependencies.
- A root target compatibility run produced one 158-byte `root:aster 0640`
  temporary report. The unprivileged `aster` user consumed it successfully and
  returned `0` high-priority events, the fixed 900-second window and digest
  `67f3403168c1f33f1c9c9517`.
- The first unprivileged compatibility attempt failed before import because the
  temporary adapter was staged mode `0600`; correcting that temporary file to
  its production mode `0644` made the consumer pass. This did not affect the
  report custody or grant journal access.
- All temporary reports, scripts and candidate files were removed. No service,
  model, route, journal, report schedule or access group changed.

Representative network, configuration, backup and log source designs are now
complete. The next gate is one combined reviewed release and a representative
five-source-or-broader no-effect investigation; it must retain observation
bounds and may require more than one bounded incident rather than increasing a
single incident without review.
