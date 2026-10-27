# Full-Aster first-screen transaction boundary — 2026-10-26

## Result

**SOURCE PASS / LIVE EFFECT STILL GATED.** A dedicated transaction now fixes
the 35B compatibility screen order instead of widening the older candidate-H
and M3 F6 controller.

The transaction requires fresh same-cycle F2–F5/admission evidence, an
independent watchdog, authenticated accepted baseline, no competing work, a
90-minute maximum outage and 15-minute restoration reserve before its first
effect. It then permits exactly one read-only backup-excluded mount, two
LXC110 stop/start pairs, one transient Qwen3.6-35B reasoning-on service, and
two sequential 60-second synthetic requests. It fixes zero retries and no
promotion.

Every failure enters a fixed recovery sequence that stops the owned candidate,
removes only the fixed mount, restarts LXC110 in its captured configuration,
verifies the exact accepted 9B/SYCL/auth/schedule baseline, restores consumers,
and releases the lease only after independent proof. Uncertain recovery keeps
state for reconciliation. Nine combined preflight/transaction tests pass.

The platform-side transient-unit command is separately source-tested against
the existing `ollama` identity, SYCL environment, one 8K slot, reasoning on,
speculation absent, the existing API-key file and restart disabled. A complete
root composition and independent mount-aware guardian must still be installed
and validated before requesting the live restart window.
