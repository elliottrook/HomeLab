# SA4 runtime-control NO-GO and corrected release — 2026-11-05

## First failed gate

After Jason approved the first canary repair, the fresh pre-effect review
stopped before creating authority. The installed root owner accepted a
caller-supplied JSON assertion that the shared lock was held and emergency stop
was armed. It neither acquired the real lock nor owned an operator stop state.
The effect modules also remained deliberately `unconfigured` outside the root
owner. Running that candidate would therefore have been unsafe and would have
failed closed.

No owner or AI-PAM signer was invoked. No grant, ledger, checkpoint, target
write, receipt, rollback, restart or route occurred. The canary remains
`19b4e02d…df1a`, the lease remains ready and production remains healthy.

## Correction

The corrected source adds a fixed runtime-control owner that:

- exclusively creates and locks `/run/aster-sa4-operation.lock`;
- creates a plan-bound operator emergency-stop state;
- verifies descriptor/path identity, custody, content and link count;
- detects an operator stop mutation before every effect/observation phase;
- removes both controls only after terminal reconciliation;
- closes descriptors but retains state on any uncertainty;
- exposes no retry path.

The root transaction owner now creates these controls itself, derives the live
preflight evidence from the owned state, and uses a fixed `lxc104` binding
context that returns every component to its prior binding after each bounded
call. Callers can no longer nominate a host or provide control evidence.

## Verification

- real lock/stop acquire, observation and terminal cleanup: pass;
- existing-lock exclusion: pass;
- operator-stop mutation and retained uncertainty: pass;
- root-owner phase/uncertainty tests: pass;
- joined disposable success and rollback branches: pass;
- complete SA4 suite: 152/152 pass;
- whitespace/error check: pass.

## State and next gate

This correction is source-only. The installed root owner remains the inert
pre-correction hash and was not invoked. Next is an exact two-file inactive
upgrade/rollback review for the corrected root owner plus new runtime-control
owner. That installation is a new effect gate. Only after it validates may a
new first-repair candidate be considered; the aborted approval is not reused.
