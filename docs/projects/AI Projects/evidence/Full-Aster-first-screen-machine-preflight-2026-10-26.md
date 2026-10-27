# Full-Aster first-screen machine preflight — 2026-10-26

## Result

**PASS for source-only admission validation. Live effects remain unapproved.**

The two-request challenger screen now has a machine-readable preflight bound to
the owner-frozen benchmark contract and exact staged artifact. It requires
same-cycle F2, F3, F4 and F5 digests; a ready and absent whole-host lease; an
armed independent watchdog with a live owner; exact accepted 9B/SYCL identity
and authenticated response; healthy guests, Aster Agent and Speech; exact
schedules; no competing work; completion of the 03:00 pull; a maximum
90-minute outage budget; and at least 15 minutes of protected restoration
reserve.

Passing produces `admitted: true` but explicitly keeps
`live_effect_authorized: false` and `authority: not-granted`. The exact restart,
mount, transient candidate and restoration transaction still needs its own
approval after fresh runtime facts exist.
