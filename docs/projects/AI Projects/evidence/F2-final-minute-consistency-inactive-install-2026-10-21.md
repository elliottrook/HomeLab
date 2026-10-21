# F2 final-minute consistency inactive installation — 2026-10-21

## Result

**PASS for inactive installation; F2 remains open.**

Jason approved the four-file inactive correction from platform commit
`223d4a18855e1085dce180a2c842fef926d1d1b8`. The change was installed on
Proxmox after re-reading every current target hash and the unchanged
coordinator pin. It did not schedule or run an archive scan, create a receipt,
acquire a lease, stop a service or call a model.

## Installed boundary

| Target | Installed SHA-256 |
|---|---|
| `f2_preflight_snapshot.py` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` |
| `f2_preflight_fixed_wrapper.py` | `0dbdbce56be6f72ada8df54dd28cfcda32f6494200ba97f4b40703496271ba9f` |
| `f2_observer_runner_candidate.py` | `27edca21a68dd9d575bbb6bd66a7b5787880f3bc590b8f6efe3457c40722aeb0` |
| `retained_archive_producer_candidate.py` | `5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf` |

The unchanged coordinator remains pinned at
`fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356`.
All four installed files are root-owned mode `0644`.

The previous four files are preserved at
`/root/aster-f2-window-consistency-rollback-223d4a18`, with a root-owned
mode-`0700` directory and mode-`0600` files.

## Target-Linux verification

The approved source was exported from the exact commit, hashed on the Mac and
again after staging on Proxmox. Installation rechecked the four expected old
hashes and the coordinator before any replacement. The rollback-safe installer
would have restored all four old files if a post-install check failed.

Target Linux passed **33/33** tests:

- 1 dependency-pin closure test;
- 9 snapshot/final-guard tests, including a fresh 01:15 snapshot accepted only
  at exactly 01:20;
- 14 observer tests, including the exact 01:20 start and 01:40 deadline; and
- 9 retained-producer tests, including the 01:20–01:29 start window and 01:40
  hard deadline.

Postchecks found:

- the whole-host lease state `ready`, with no lease or lock;
- both recurring F2 timers disabled and inactive;
- no F2 scanner or `zstd -t` child;
- no F2 archive-integrity receipt;
- LXC104, LXC110 and LXC116 running;
- `aster-agent`, `aster-llama` and `aster-speech` active in their guests; and
- `pvescheduler` and `pvestatd` active.

Temporary installation files were removed after verification.

## Consequence

The two source contradictions exposed by the failed October 21 attempt are now
corrected on the inactive installed path: F2 no longer depends on the future
02:00 LXC110 mirror, and all final-stage components agree on the 01:20 start
and 01:40 deadline. This does not turn the failed October 21 cycle into a pass.
A fresh cycle still needs an exact activation card and separate authorization;
only a supervised three-archive exit-zero result can complete F2 and unblock
F3.
