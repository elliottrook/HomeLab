# F4/F5 October 28 missed-window result

## Decision

**TIMED TEST: NO-GO — F4/F5 were not invoked.**

The October 28 F2 and F3 gates completed successfully. TrueNAS task 3 at
02:00 and task 2 at 03:00 also completed successfully, and the 03:50 workload
resume restored the News, Paperless and EPUB scheduling boundary. The F3
receipt remains root:root `0600`, one link, with digest
`1e05f475f09579dd7bb23a3938b2f21200ff7f62f7dd668ff9eb7ab695a4a3dd`.

No approved one-shot F4/F5 invocation was scheduled after the 03:00 pull. The
continuous Stream A heartbeat next resumed at 05:06 PDT. By then the installed
root writer's retained-integrity verifier could no longer accept the F3
receipt: its fixed three-hour freshness bound expired at approximately 04:34,
and the separate full-Aster outer completion cutoff of 04:15 had already
passed. The writer was not invoked, no F4/F5/admission artifact was written,
and no lease, stop, restart or model call occurred.

This was a scheduling and approval-sequencing failure, not an F2/F3 or backup
failure. The safe correction is to prepare and review a complete next-cycle
conditional chain before the overnight window. It must include a one-shot
F4/F5 invocation shortly after the successful 03:00 pull, conditional on fresh
same-date F2/F3 bytes, exact task 2/3 completion, ready lease, absent targets
and healthy production. Approval must be obtained before that window; a normal
four-hour continuation heartbeat cannot own a 03:00–04:15 effect chain.

The next card must also replace the fixed 03:50 caller resume with lease-aware
ownership if any F6/full-Aster effect can remain active then. It may not extend
the current receipt, retry October 28, weaken the verifier freshness bound or
infer F4/F5 from successful F2/F3.
