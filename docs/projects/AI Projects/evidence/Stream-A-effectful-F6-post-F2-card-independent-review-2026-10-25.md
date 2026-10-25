# Stream A effectful F6 post-F2 card — independent review

> Decision: **REVISE BEFORE LIVE APPROVAL**
>
> Platform source: `ef1d1842500eada333341f659a6099a6390dec51`
>
> Card SHA-256: `93926889f8a0f779f56b25f10a9fb57208bfe31de72d8239ba1479bc50edb23d`

The card correctly keeps F6 live-blocked on fresh F2–F5 evidence, separates
arming from quiescence, orders D4 before M3, preserves the restoration reserve
and forbids automatic retry. It is a sound dependency outline. It is not yet
an executable or approval-ready effect card.

## Required corrections

1. **Correct D4 custody wording.** The temporary candidate-G tar on the Mac is
   owner-only mode `0600` and owned by the local user, not root. Root custody
   applies only after a future validated guest-side staging transaction. The
   archive remains SHA-256
   `d5a36cd02be6fdd3d0935e6ca1b23c1d0cad1329d72b04bb4048505fec7e3d47`
   with exactly 11 members.
2. **Preserve the existing candidate-G authorization accurately.** Jason's
   exact candidate-G run plus conditional blind review is recorded as approved
   and unspent at run digest
   `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`.
   The future card may still require a fresh effectful F6 activation decision,
   but it must not imply that the already-recorded candidate authorization was
   consumed or silently replaced. M3 retains its distinct recorded live gate.
3. **Pin the effect transaction.** Before an approval request, freeze the exact
   installed controller, adapter, observer, owner, watchdog, heartbeat and
   callback hashes; exact owner/intent/lease/generation identities; commands
   for arm, acquire, quiesce, post, cancel/recover and cleanup; maximum lease
   duration; outer wall deadline; restoration reserve; four-consumer baseline;
   output/journal locations; and rollback checkpoint. Name the independent
   postcheck that proves every mask, service and timer returned to its prior
   state.
4. **Bind fresh evidence rather than naming it generically.** The eventual
   card must identify the exact F2 result, F3 receipt, F4 binding and F5
   observation digests and require them to belong to the same accepted backup
   cycle. It must bind the M3 staging-manifest SHA-256
   `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`
   and D4 run digest above.

## Current decision

No activation, lease, consumer effect, packet copy or model call is authorized
by this review. The D4 and M3 packets remain static-ready and unspent. The
October 26 F2 exact-date timers remain the next volatile dependency and must
not be changed. Once the platform owner supplies a corrected hash-pinned card,
Stream A can review it offline while waiting for F2.
