# A1 host artifact source review — 2026-10-14

Review scope: offline source and command-boundary review of the A1 unit,
launcher, hash-bound key helper, application watchdog and installation
manifest. No host command, service start, credential operation or firewall
change was performed.

## Reviewed hashes

| Artifact | SHA-256 |
|---|---|
| `aster-a1-test.service` | `26de2dce3a7d7521be4c1760a3e05dda6378aeb3c773cff7aff38c8355183b21` |
| `a1_service_runner.py` | `feae2ec1f423ec4cbcde33112a64ed6db0963a6c3868726bcdff732b07b520c1` |
| `aster-llama-test-key-remove` | `0c294198d2e60b5ed07654c92025713ca6a812bdd065720f3d8183ae6ef357d6` |
| `a1_key_file.py` | `018340fe0bf8a7ec7526d2d0709d21cc8f11fcef6c252cdbfeb6798cc6a055cd` |
| `application_b60_watchdog.py` | `cf3642a04094cf5626b344aaa4a0ed403d27db2e1e100aee5f4173b8478d45e3` |

## Findings

- The unit starts exactly one unprivileged worker on port 19104 and allows
  only loopback plus the llama backend at the systemd address-filter layer.
  It does not refuse the platform controller's intentional start/stop.
- The launcher imports the guarded factory before serving; invalid config,
  missing owner-only custody or privileged settings fail before Aster import.
- The key helper checkpoints atomically, preserves the production line, and
  preserves the observed key-file owner/group/mode, and removes only the one
  line whose SHA-256 matches the root-owned test digest. The pre-add checkpoint
  is create-once and immutable; unknown, ambiguous or drifted removal fails
  closed.
- The application watchdog owns all five application effects: sidecar stop,
  ingress-policy restore, test-key removal/reload, production-auth postcheck,
  and consumer restore. It never starts consumers after an auth or policy
  failure and retains the lease state on uncertainty.
- The controller now separates pre-lease checkpoint validation from post-lease
  sidecar admission. Its direct restore path is disabled; only the application
  watchdog may restore consumers. It persists the armed state and both
  deadlines before the first consumer stop; subsequent key/firewall effects
  are therefore under watchdog authority.
- The watchdog requires an armed deadline, records intent/observed events and
  refuses to replay an uncertain effect after a crash. It distinguishes the
  start-by deadline from the final restore deadline; a late tick still runs
  safe recovery and reports `overdue` rather than abandoning effects.
- The manifest rejects a container-wide nftables rule because LXC104 also hosts
  production Aster; temporary backend exclusivity requires a checkpointed
  LXC110 ingress policy and positive allowed/denied observations.

## Remaining gates before live approval

1. Merge or otherwise make the pinned Stream A A1 source bundle available in
   this branch; the manifest currently references commit `72566b5f` in the
   handoff worktree.
2. Implement and review the fixed LXC110 ingress-policy apply/restore helper;
   the current artifact set deliberately contains only the restore contract,
   not a broad ruleset replacement.
3. Validate the platform receipt producer's application-mode state transition,
   including the planned-identity to persisted-lease to real-receipt order,
   then sidecar admission.
4. Install and validate the fixed host helpers for ingress-policy apply/restore,
   hash-bound key removal/reload and watchdog scheduling.
5. Validate the host-specific UID, Mini source address, existing firewall
   chain, systemd version and exact Aster dependency bundle read-only.
6. Run the no-effect preflight and independent host observer checks. Any
   mismatch keeps the live A1 run blocked.
