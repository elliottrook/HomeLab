# M1/D4 fixed Doctor usefulness inactive install result — 2026-10-25

Status: **PASS — INSTALLED INACTIVE**

Jason approved the exact inactive installation. At 22:41–22:43 PDT, Stream A
transferred and reverified the packet from source commit `abcaa595`, then ran
the frozen transaction in
`scripts/aster-adaptive/install_fixed_doctor_usefulness_inactive.sh`.

## Installed boundary

- deterministic archive SHA-256:
  `7c89cd3a46bfbcff52257e35d0473c9954eb7a73f43ec91f5b54b79f7a1f50ea`;
- target: `/var/lib/aster/fixed-doctor-usefulness-v1` in LXC104;
- custody: root-owned mode `0700` directory with exactly eight root-owned
  mode-`0600` regular files;
- opened-byte result: eight inputs and 29,892 bytes matched the frozen
  manifest;
- the installed validator, imports and runner help path passed on target
  Linux with bytecode generation disabled; and
- the temporary Proxmox and guest transport files were removed by the
  transaction.

Independent post-install inspection re-read all eight installed SHA-256
identities and found no extra object, subdirectory, bytecode cache, answer
output, attempt journal or usefulness runner process. The existing fixed
Doctor gateway and caller are production services from the earlier approved
read-only capability; this installation neither changed nor restarted them.

## Production and schedule postcheck

LXC104, LXC110 and LXC116 remained running. `aster-agent.service`,
`pvescheduler` and `pvestatd` remained active, and the whole-host lease
reported `ready`. The October 26 F2 prepare and final timers remained scheduled
for 01:15 and 01:20 PDT respectively; both recurring timer templates remained
disabled. No lease, lock, receipt, route, authority grant or model request was
created.

This closes inactive custody only. The usefulness run remains blocked on fresh
F2–F5 evidence, an admitted and independently recoverable F6 workload, and a
separate exact effectful run approval. The staged files do not authorize a
model call or routing promotion.

An exact [source-only removal card](M1-D4-fixed-doctor-usefulness-inactive-removal-card-2026-10-25.md)
pins all eight installed hashes and refuses recursive deletion or removal after
any output, journal, cache, process or extra object appears. It has not been
executed and grants no removal authority.
