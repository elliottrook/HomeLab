# Full-Aster first-screen transaction boundary — 2026-10-26

## Result

**SOURCE PASS / LIVE EFFECT STILL GATED.** A dedicated transaction now fixes
the 35B compatibility screen order instead of widening the older candidate-H
and M3 F6 controller.

The transaction requires fresh same-cycle F2–F5/admission evidence, an
independent watchdog, authenticated accepted baseline, no competing work, a
30-minute effect window and 15-minute restoration reserve before its first
effect. It then permits exactly one read-only backup-excluded mount, two
LXC110 stop/start pairs, one transient Qwen3.6-35B reasoning-on service, and
two sequential 60-second synthetic requests. It fixes zero retries and no
promotion.

Every failure enters a fixed recovery sequence that stops the owned candidate,
removes only the fixed mount, restarts LXC110 in its captured configuration,
verifies the exact accepted 9B/SYCL/auth/schedule baseline, restores consumers,
and releases the lease only after independent proof. The unprivileged LXC110
mapping is explicit: the root-staged artifact is temporarily mapped to guest
`ollama` only after the drain, then root:root 0400 file and 0700 directory
custody are restored before the accepted baseline and lease can pass recovery.
Uncertain recovery keeps state for reconciliation. Five boundary tests pass.

The platform-side transient-unit command is separately source-tested against
the existing `ollama` identity, SYCL environment, one 8K slot, reasoning on,
speculation absent, the existing API-key file and restart disabled. A complete
root composition and independent mount-aware guardian must still be installed
and validated before requesting the live restart window.

## Complete inactive packet review

Platform commit `b6dc186eef865924294b4e5cb1ef72d73c149733` now supplies the
complete root composition, workload-specific admission, same-process recovery,
independent deadline guardian, fixed observer, two-request helper and inert
launcher. Its 22 focused first-screen tests, 11 F4/F5 tests and 62 existing
full-drain regression tests pass. The controller also cleans up only exact
root-custodied evidence it created when a failure occurs before any drain; once
a drain is attempted, durable state is retained until exact recovery succeeds.

The exact inactive-install card is platform commit `cec8050f`. Its 11-row
manifest contains nine new files and two replacements with recomputed SHA-256
pins. Read-only target inspection found every new target absent, both replaced
F4/F5 predecessors exact, all imported full-drain dependencies exact and the
whole-host lease ready. This is **approval-ready for inactive installation**;
it creates no service or timer and authorizes no restart, mount, lease, model
request or live effect.

Jason approved that exact inactive install. Platform result commit `16a6cd27`
records a pass: all eleven installed hashes/custody match, and target Linux
passed 22 first-screen, 11 F4/F5 and 62 full-inference tests. The wrapper and
guest helper both refused live work without their effect flags. The lease
remained ready; runtime evidence, locks and mounts remained absent; the
evaluation timers remained disabled/inactive; and the three guests, Aster
Agent, accepted 9B/SYCL, Speech and Proxmox daemons remained healthy. No model
call or restart occurred. The next dependency is the already scheduled fresh
F2/F3 cycle, followed by same-cycle F4/F5 and a distinct live-restart approval.
