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

## Revision check — platform `d6388942`

The first revision corrects D4 custody, binds both workload digests and adds
the 4,500-second hard / 5,400-second restore deadlines plus a phase sequence.
Those changes close findings 1, 2 and the timing portion of finding 3.

The card is still **REVISE BEFORE LIVE APPROVAL** because the transaction is
descriptive rather than executable. It does not list the installed source
hashes, exact binary/callback paths, four unit names, fixed intent path,
identity path, rollback checkpoint, journal/output paths or complete command
arguments. It still contains the placeholder `<0600-root-intent>`. Those
values must be frozen from the accepted installed cards so an operator cannot
choose them during the live window. The same-cycle F2–F5 evidence remains
necessarily pending until runtime.

## Second revision check — platform `6981743b`

The second revision adds source digests, wrapper/callback names, four consumer
unit names, state and identity paths, fixed intent names, restoration timing,
one rollback checkpoint and lease-entrypoint command shapes. Its card SHA-256
is `d5f39d14d61e5fc54823b3c16334bba02480f9807148c6a2791a49b1c78d116b`.

It remains **REVISE BEFORE LIVE APPROVAL** for four concrete reasons:

1. The source table gives basenames rather than the full installed paths, so it
   still does not uniquely bind the files the live wrapper imports.
2. Arm, recovery and cleanup remain prose rather than exact invocations and
   complete fixed payloads. The acquire, post, outcome and restore intent JSON
   objects are also not frozen to the entrypoint's exact schemas.
3. The D4 and M3 sections invoke only the lease bookkeeping `start` and
   `outcome` phases. They do not name the actual workload runners or their
   exact arguments, credentials boundary, deadlines and evidence paths. Those
   phases cannot themselves perform either model workload.
4. The card requires the lease to bind F2/F3/F4/F5 digests, but the installed
   acquire intent schema accepts only `backup_receipt`, `f2_receipt` and
   `f3_receipt`. The card must either identify the separately verified F4/F5
   binding mechanism or revise the controller under a new reviewed inactive
   change. A live operator cannot improvise extra fields because the
   entrypoint rejects non-exact intent keys.

These are pre-effect specification gaps. No host change is needed to observe
them, and the October 26 F2 timers remain undisturbed.
