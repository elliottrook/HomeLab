# M3 NLU calibration inactive staging result — 2026-10-25

> Result: **PASS — CORRECTED PACKET STAGED INACTIVE**

Jason approved the corrected staging packet at Stream A commit `11bf4733`.
The transaction copied the exact eleven inputs into
`/var/lib/aster-nlu-calibration/nlu-calibration-v1` in LXC110. Both the incoming
and final-path custody checks reported:

| Check | Result |
|---|---|
| manifest SHA-256 | `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165` |
| declared and verified inputs | 11 / 11 |
| aggregate bytes | 98,414 |
| custody | root-owned directory `0700`; files `0600` |
| authority | `not-granted` |
| target imports | pass with bytecode writes disabled |

Postchecks found exactly the eleven inputs, no `run.json`, no
`attempt-journal.jsonl`, no `__pycache__` and no Python calibration runner.
The temporary Proxmox transport files were removed. The lease controller was
`ready`; Aster Agent, Speech, the accepted llama service, `pvescheduler` and
`pvestatd` remained active.

The October 26 F2 one-shot timers remained enabled for 01:15 and 01:20 PDT and
the current-cycle result was absent, as expected before the run. An initial
postcheck queried obsolete `local-ai-f2-*` unit names and returned not-found;
the actual `f2-preflight-*-20261026.timer` units were then verified unchanged.

This pass closes inactive M3 packet staging only. No lease, model request,
score, threshold selection, route change, service interruption or F2 action
occurred. A compatible effect adapter and an approved live evaluation window
remain necessary before the staged packet can run.
