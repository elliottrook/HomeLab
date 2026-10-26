# M3 NLU score-boundary first inactive install — NO-GO

> Observed: 2026-10-25 23:30 PDT
>
> Result: failed closed before any installed packet change

The approved four-file transaction stopped during prestate inspection because
it incorrectly treated the stage validator and stage manifest as installed
members of the eleven-file LXC110 packet. They are temporary validation inputs,
not staged packet members. The first missing path was
`nlu_calibration_stage_manifest.py`.

The transaction had not reached its `started` boundary. Independent postcheck
confirmed the actual directory still contains exactly its eleven expected
root-owned mode-`0600` files; the scorer and journal retain their old hashes;
and no output, attempt journal, bytecode cache or NLU process exists. The lease
is `ready`, accepted llama remains active, and both October 26 F2 timers remain
active. Exact temporary transport files were removed. No model call, lease,
service stop or F2 change occurred.

The corrected transaction now checkpoints and replaces only the installed
scorer and journal. It uses the new validator and manifest from temporary
root custody solely to validate the resulting eleven-file packet. Its offline
syntax and transaction tests pass 2/2. Because the file boundary changed, the
failed approval is consumed; the corrected two-file installation requires a
new exact approval and must finish before the backup exclusion margin.
