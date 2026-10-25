# Stream A evaluation-lease effect-entrypoint inactive install — 2026-10-25

> Result: **NO-GO; automatic rollback passed**

Jason approved the exact inactive upgrade reviewed in
`Stream-A-evaluation-lease-effect-entrypoint-review-2026-10-25.md`. The
transaction was limited to one checkpointed replacement and two additions:

- installed `evaluation_lease.py` old SHA-256
  `38a986e9d868d04c7ee7814ae0fbd2f1a1709e7a464916195d594ca2bf286312`
  to candidate SHA-256
  `675ebb566de298334f7c612cae9af2637067930f40c0ad2c23a22e1b7e248f1b`;
- add `evaluation_lease_entrypoint.py` at SHA-256
  `e4efd62036b8d26b0eb972a03f53f2cfdf6fbb6fa8a00f1c652b5803c23b5ce7`;
  and
- add `/usr/local/sbin/stream-a-evaluation-lease` at SHA-256
  `962100b591493b2ae8f62814fa6f66a1875463dd5ca613bb321169764c56c276`.

The source packet, validation packet and transaction driver matched their
reviewed hashes before execution. All 32 target-Linux tests passed and all five
installed Python modules parsed and imported. The transaction then failed its
final exact-directory postcondition after the disabled wrapper invocation.

## First failed boundary

The reviewed wrapper invokes `/usr/bin/python3` without `-B`. Its real
disabled-mode invocation imports the installed modules and creates
`__pycache__`. The response itself is the expected effect-free JSON, but the
new directory entry violates the card's exact five-file and no-bytecode
postcondition. The validation driver therefore exited non-zero and invoked its
rollback trap.

This is a release-packet defect, not a target service or lease failure. The
wrapper must invoke `/usr/bin/python3 -B`, its hash and card pins must be
updated, and a real wrapper regression must prove that disabled invocation
leaves no bytecode before another inactive installation is considered.

## Rollback and postcheck

The automatic rollback restored the old `evaluation_lease.py` byte for byte,
removed the candidate entrypoint and wrapper, and retained the root-owned
mode-`0600` rollback checkpoint. Independent read-only checks confirmed:

- the original four library files and their prior hashes/modes are the only
  files in the installed directory;
- no `__pycache__`, evaluation lease state or operation lock remains;
- `local-ai-lease status` is `ready`;
- LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
  `pvescheduler` and `pvestatd` are healthy; and
- the October 26 F2 exact-date timers remain enabled and active for 01:15 and
  01:20 PDT.

No effectful phase, lease, consumer stop, model request, F2 action, D4 run or
M3 run occurred. The platform owner received the exact correction request.
The evaluation-lease entrypoint is **NO-GO** pending a new hash-pinned source
and card plus a new exact inactive-install decision. The independent October
26 F2 test remains **GO — SCHEDULED / CONDITIONAL** on its fresh runtime gates.

## Corrected candidate ready

The platform owner supplied implementation commit
`b18302f31b0b0e23bfae7476b737d775a1e38df8` and metadata/card commit
`6bf5f2526a944649fe9b81a552aec840414c9b6b`. The only runtime-file change from
the failed candidate is the wrapper's `python3 -B` invocation. The updated
card is SHA-256
`7303414ef238e158ecfef5548affeba20728ef4dd65e1e49afa8d22c202fec7f` and the
wrapper is SHA-256
`15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af`.

Independent clean-archive validation reproduced 33/33 tests, including a real
disabled wrapper invocation that leaves exactly the five source files and no
bytecode. The unchanged contract and entrypoint hashes still match the card.
The corrected local install, validation and transaction artifacts are:

- install packet: `fc51412ddec35318a8befe81bf962523ada6b475cc848f97c0e48cfd7941324c`;
- validation packet: `2cfedd7dc13fa7d49f4fa0533ef0efd35ef5532b9984573e06e34179366818cd`;
- transaction driver: `a8c438d31d748b4d78d651dc5e43256123b1cc68e3823eabab3f42a59fd27193`.

The driver accepts the retained checkpoint only when its directory and file
custody and old source hash match exactly. A new exact approval is required
because the wrapper and transaction artifact hashes differ from the failed
attempt.

## Corrected inactive installation result

Jason approved the corrected inactive installation. Two transaction-package
checks failed closed before the final pass:

1. the first corrected attempt found the prior failed candidate's two-file
   `__pycache__` residue before changing any source; those two verified Python
   bytecode files were removed to complete the prior rollback; and
2. the next attempt installed the candidate, then its 33-test validation failed
   because the validation archive had flattened the repository paths required
   by the new wrapper regression. Its trap restored the exact old four-file
   baseline and left no state or lock.

The final validation packet preserved the clean commit hierarchy and passed
33/33 tests locally before transfer. Its exact artifacts were:

- install packet: `9ff50aff53b141714504dd947ade0a50df514db66ff349fcf0c540ca6c3c50c3`;
- validation packet: `3c357a797dafe1482b77be79449614beae3eaf2581d6a4ad1eda757cb0791506`;
- transaction driver: `a04069c279e3f93c3dccdd9b7732da36297f1bd755e190a8a6f58e8b69f5aa51`.

The final target transaction passed 33/33 tests, installed imports, the real
disabled wrapper invocation and exact no-bytecode postcondition. Independent
postchecks confirmed the five root-owned mode-`0644` Python files, root-owned
mode-`0755` wrapper and every pinned hash. The old contract checkpoint remains
root-owned mode `0600` in a mode-`0700` directory. No lease state, operation
lock, unit, timer, consumer change or model request exists. `local-ai-lease`
is `ready`; LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` are healthy.

The inactive entrypoint installation is **PASS**. Live effects remain disabled.
The next platform dependency is the separately reviewed and activated
independent watchdog/recovery boundary. Fresh F2/F3/F4 evidence and a separate
live evaluation authorization remain mandatory before any consumer stop or
model request.
