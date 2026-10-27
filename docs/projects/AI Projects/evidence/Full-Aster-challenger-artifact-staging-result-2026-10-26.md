# Full-Aster challenger artifact staging result — 2026-10-26

## Result

**PASS — exact candidate artifact staged and verified; not mounted or loaded.**

Under Jason's exact staging approval, the Proxmox host downloaded the pinned
maintainer artifact from repository
`ggml-org/Qwen3.6-35B-A3B-GGUF`, revision
`baec3ebee244827cda0f4557eafa8b28f7545fa6`.

Verified installed identity:

- path:
  `/var/lib/vz/aster-model-staging/qwen36-35b-a3b-v1/Qwen3.6-35B-A3B-Q4_K_M.gguf`;
- bytes: `20,419,565,568`;
- SHA-256:
  `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`;
- custody: root:root, mode `0400`;
- completion mtime: `2026-10-26 19:17:30.950282081 -0700`;
- host free bytes after staging: `39,051,284,480`, above the 20 GiB retained
  floor.

Postcheck found `local-ai-lease` ready, LXC 110's accepted service
active/running with zero restarts, the accepted model symlink still resolving
to the exact pinned 9B blob and no LXC 110 mount-point entry. The staged model
has therefore not entered the guest or a serving process.

This completes artifact acquisition only. Architecture compatibility, GPU/KV
residency and two-request structure still require a separately reviewed F6
effect transaction because they must temporarily isolate consumers and replace
the accepted serving process. The 00:30 backup and October 27 F2/F3 schedule
remain untouched.
