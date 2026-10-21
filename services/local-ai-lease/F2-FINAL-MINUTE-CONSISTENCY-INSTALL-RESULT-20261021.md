# F2 final-minute consistency installation result — 2026-10-21

Status: inactive source installation completed and validated; activation was
not performed. Platform evidence commit: `223d4a18855e1085dce180a2c842fef926d1d1b8`.

The four approved source corrections were installed without changing timers,
services, schedules, terminal state, receipts, leases, or production services.

| Installed path | SHA-256 | Rollback source |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` | `/root/aster-f2-window-consistency-rollback-223d4a18/f2_preflight_snapshot.py` |
| `/usr/local/libexec/local-ai-lease/f2_preflight_fixed_wrapper.py` | `0dbdbce56be6f72ada8df54dd28cfcda32f6494200ba97f4b40703496271ba9f` | `/root/aster-f2-window-consistency-rollback-223d4a18/f2_preflight_fixed_wrapper.py` |
| `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` | `27edca21a68dd9d575bbb6bd66a7b5787880f3bc590b8f6efe3457c40722aeb0` | `/root/aster-f2-window-consistency-rollback-223d4a18/f2_observer_runner_candidate.py` |
| `/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py` | `5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf` | `/root/aster-f2-window-consistency-rollback-223d4a18/retained_archive_producer_candidate.py` |

The coordinator remains pinned at
`fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356`.
Rollback directory custody is 0700 with files 0600.

Target Linux validation passed 33/33 tests: 1 dependency-pin closure, 9
preflight snapshot, 14 observer, and 9 retained-producer tests. Temporary
staging was removed.

Post-install state: recurring F2 timers disabled/inactive; lease ready; no
lease, lock, receipt, or scanner; guests 104/110/116 and aster-agent,
aster-llama, and aster-speech healthy. No activation or scheduled run occurred.
