# M3 NLU score-boundary third inactive install — NO-GO

> Observed: 2026-10-25 23:37 PDT
>
> Result: packet and tests passed; invalid final import rolled back

The approved revised transaction passed prestate, installed the two candidate
files and validated all eleven packet files at 99,805 bytes. All nine target-
Linux scorer tests passed. The following final import check failed only because
it named `nlu_calibration_stage_manifest`, which is a temporary validator and
is deliberately not an installed packet module.

The transaction rolled back both installed files. Independent postcheck
confirmed the old scorer and journal hashes, absent output/journal/cache/test
tree, lease `ready`, accepted llama active and both October 26 F2 timers active.
No model call, service stop, lease or F2 change occurred.

The revised transaction removes only that invalid temporary-validator import.
It retains the already passing full packet validation, all nine target tests
and imports the three installed runtime modules: runner, scorer and journal.
Offline syntax and transaction tests pass 2/2. Another attempt requires new
exact approval.
