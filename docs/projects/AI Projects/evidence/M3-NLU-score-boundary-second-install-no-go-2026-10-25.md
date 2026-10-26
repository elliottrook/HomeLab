# M3 NLU score-boundary second inactive install — NO-GO

> Observed: 2026-10-25 23:34 PDT
>
> Result: candidate packet validated; target test-layout failure rolled back

The approved corrected two-file transaction passed its prestate checks,
checkpointed the old scorer and journal and installed the two candidate files.
The candidate then passed full eleven-file custody and hash validation at
99,805 bytes with manifest digest
`7b547d9b38d3be1d951e2d8cbeee011a723f8582006c0885ad37d01f5388ee80`.

The target scorer test did not start because its unchanged helper imports the
public development fixture relative to its test module, while the transaction
placed that helper directly in `/tmp` without `/tmp/fixtures/`. Python raised
`FileNotFoundError` for the missing public fixture. This is a transaction test
layout defect, not a scorer assertion failure.

Rollback restored the old scorer and journal hashes. Independent postcheck
confirmed exactly eleven root-owned mode-`0600` packet files; no output,
journal, cache or runner process; lease `ready`; accepted llama active; and
both October 26 F2 timers active. Exact temporary paths were removed. No model
call, service stop, lease or F2 change occurred.

The revised transaction builds a unique temporary test root, places both test
modules under their normal names, copies the already staged public development
fixture into its expected `fixtures/` subdirectory, and removes that exact
temporary tree after validation. Offline syntax and transaction tests pass
2/2. A new approval is required before another installation attempt.
