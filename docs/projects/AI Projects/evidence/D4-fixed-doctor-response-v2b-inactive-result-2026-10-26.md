# D4 fixed Doctor response v2b inactive result — 2026-10-26

## Result

**PASS / INACTIVE.** The freshness-corrected two-file candidate from source
commit `57487bc3` is installed at
`/opt/aster-agent/candidates/fixed-doctor-response-v2b` in LXC104.

- caller SHA-256:
  `d1b567a8c7f0f205a6bd3fdc4d397ba03355f695995de74337fc4848e0cf9e48`;
- response SHA-256:
  `4ca8721b1076815de3220dc51a1e499fd6822f3a9a1085bfc561804bea065298`;
- target-Linux focused suite: 8/8 passed;
- the suite covers the measured 13,622-second failure range and exact
  129,600-second source boundary.

## Live-state proof

After staging, the live caller retained predecessor SHA-256
`aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a`,
the live response module remained absent, and the fixed caller and Aster Agent
were active with zero reported automatic restarts. No service was restarted.

The first combined postcheck attempted one command substitution on the
Proxmox host rather than inside LXC104 and exited nonzero after the successful
test. A separate correctly scoped LXC postcheck established all of the live
facts above. This was a verification-command quoting error, not a target or
service failure.

## Next gate

The corrected cutover remains a caller-only restart with automatic rollback.
It requires owner approval immediately before execution. No broader stack
restart, route change, authority grant or model call is part of that effect.

