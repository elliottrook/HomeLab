# SA3 candidate-g capture-projection correction — 2026-11-04

## R5 result

Fresh booking `aster-stream-a-sa3-envelope-20261104-1430-r5` claimed exactly at
14:30:00 and ended NO-GO at 14:33:06, after 186 seconds. Terminal state was
`OWNER_TRANSACTION_FAILED_RESTORED`, first phase `owner-transaction`, with
`production_restored=true`. No result file was retained. The owner error again
ended `unclassified guest failure` despite the installed class-only wrapper.

Independent restoration passed: lease ready, Doctor healthy/no codes, no
drain/shared lock, listener, transient scope or candidate process; production
services and schedules healthy with zero core restarts. R5 is spent and cannot
be retried.

## Measured transport fact

A content-free target probe ran `pct exec 110` with a guest process that wrote a
bounded JSON code to stderr and exited one. Proxmox returned that JSON on the
host subprocess's stderr, not stdout. This disproves the initial channel-swap
hypothesis for the simple case. R5 therefore most likely had no bounded JSON
object, but its deleted raw capture prevents claiming the exact failure shape.

## Source-only correction

The host adapter now projects failure evidence in this strict order:

1. a bounded `code` from a standalone or prefixed JSON object on stderr;
2. the same bounded code on stdout;
3. only the final valid traceback class name, excluding its message;
4. only process exit status and stdout/stderr byte counts;
5. the conservative unclassified fallback if even those fields are invalid.

It never retains raw text, prompts, answers, case IDs or exception messages.
The corrected adapter SHA-256 is
`101ce58e6e103db22b9da9532528e44ac84171e178a5baeee0a4e196fe3e3c9f`.
The matching v7 manifest SHA-256 is
`1d18a86d756e6388a72794f74f3299611234be43937c12c32159f976556d9537`.

The focused source suite passes 30/30. Direct target proof passed against an
actual content-free `pct exec` nonzero capture, synthetic traceback projection,
and empty-capture exit telemetry. The exact target staging directory was
removed.

## Boundary

This is source-only. A reversible inactive host-adapter/manifest installer and
installed-path proof are required before another booking. No retry, model call,
restart, backend change, blind review, route, tool grant or promotion follows.
