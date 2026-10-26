# Stream A M1 authority reconciliation and F6 next gate — 2026-10-25

**Status:** M1 authority evidence available; effectful F6 remains **REVISE BEFORE LIVE APPROVAL**.

**Authority result:** `4fd5761b6a4c27c5c1e53954c842e21d207de03e`

## Newly available M1 evidence

The fixed Doctor activation completed from exact source `122b566164ee923bc227dc9b95c423b6e1db6c06` using activation script SHA-256
`1dbfadd48df75565851df0d620f10e80f4c9805eea44df037afad3b2c93df440`.

Independent live postchecks recorded:

- UID 978 is the sole fixed-Doctor observer;
- exactly one Green, non-probationary `diagnostic.aster-inference.latest` grant exists;
- exactly one fixed request was consumed;
- the caller and gateway are active and enabled with zero restarts;
- the ordinary broker and Aster Agent are healthy with zero broker restarts;
- SQLite integrity is `ok`;
- the Forgejo project-document capability remains Yellow, non-probationary and enabled; and
- the root-only rollback checkpoint is retained.

No model call, ordinary Aster route, Forgejo write, or broader authority was enabled. This is authority evidence for the one fixed Doctor read only. It does not authorize F6, consumer quiescence, a model workload, or automatic routing.

## Exact F6 decision

The effectful F6 card remains blocked. The new M1 evidence closes the Doctor-authority prerequisite, but does not close the platform transaction gaps identified in the independent review at `Stream-A-effectful-F6-post-F2-card-independent-review-2026-10-25.md`.

The next effectful card must be a new, hash-pinned transaction card with all of the following frozen before any live approval:

1. **Installed paths, not basenames.** Bind every controller, adapter, observer, owner, watchdog, heartbeat and callback file to its full installed path, exact SHA-256, owner, group and mode. Use the already installed inactive packet as the source of truth; do not copy hashes from the older rejected packet.
2. **Exact phase payloads and commands.** Freeze complete JSON objects and exact invocations for arm, acquire, owner launch, heartbeat, quiesce, post, D4 start/outcome, M3 start/outcome, cancel/recover, restore and cleanup. The card must state which commands are content-free and which can stop or start consumers. No operator-selected fields or paths are permitted.
3. **Real workload runners.** Name the exact D4 and M3 runner paths, hashes, arguments, input manifests, output/journal paths, credential boundary, per-run deadline and terminal-result checks. Lease bookkeeping phases alone are not workload execution and cannot be presented as such.
4. **F4/F5 binding.** The installed acquire schema accepts only `backup_receipt`, `f2_receipt` and `f3_receipt`. Therefore the next card must either bind F4/F5 through an already reviewed, separate durable admission artifact or first install and review a controller correction under a new inactive card. It must not improvise extra acquire fields or merely name F4/F5 in prose.
5. **Same-cycle evidence.** Bind the exact accepted F2 result, F3 receipt, F4 binding and F5 observation digests to the same successful backup cycle. Preserve the already approved and unspent Candidate-G authorization at run digest `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153` and the M3 staging manifest digest `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
6. **Independent recovery proof.** Name the independent postcheck that proves every consumer mask, service, timer, lease lock, operation lock, heartbeat, intent and restore path returned to its prestate. Require explicit healthy/unconfirmed recovery reporting and retain the rollback checkpoint.

## Boundary

This reconciliation is source/documentation only. It performs no lease arm, acquire, consumer stop, model request, D4/M3 run, F2 change, F6 activation, platform mutation or Git push. The next approval request is not valid until the exact paths, payload schemas, workload runners and F4/F5 admission binding above are represented in a fresh card and independently reviewed.
