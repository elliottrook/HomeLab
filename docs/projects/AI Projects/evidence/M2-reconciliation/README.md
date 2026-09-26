# Adaptive work reconciliation — 2026-09-25

Status: local integration candidate; no production change or remote write by this task.
Base: `f25df1812b7ef339acb9cb59339c704a4032ea26`.
Local lineage: `1a8fa680908eac8e0b7bb76845a0b1b061e593d7`.
Isolated worktree: `/private/tmp/aster-m2-reconcile-f25`.
Branch: `codex/aster-m2-reconcile-20260925`.

## What changed during investigation

The first read-only comparison saw `origin/main` at `a86a428` and ten local commits
not in that history. During comparison the AI-PAM owner completed its separately
authorized publication of `f25df18` and reported a matching GitHub mirror. This task
made no fetch, push or remote change. All subsequent comparisons pin full commit
IDs so a moving tracking ref cannot silently alter the integration decision.

`f25df18` already contains the seven local commits through `a08114b`, plus the
remote M2/M3/M4 work and AI-PAM's explicit a5e supersession/ported coverage. Its
broker core matches the deployed Stage1 hash. The older all-at-once a5e design is
not a newer deployed authority implementation. Its applicable requirements were
mapped/ported by AI-PAM; raw grant/capability edit-and-restore remains an explicit
management gate. See [supersession map](../M1-a5e-supersession.md).

## Commit map and disposition

Stable patch IDs and full ancestry results are retained in [commit-map.json](commit-map.json).
No exact patch-ID equivalent existed for the three remaining M2 commits in the
initial remote comparison. Their conceptual overlap still required review.

| Local commit | Remote representation / disposition |
|---|---|
| `39221b7` core authority candidate | Contained through AI-PAM integration; exact deployed core retained, expanded tests retained |
| `09de3b7` Synology/DNS | Contained; unrelated to M2, do not replay or edit |
| `9f11b70` M6-compatible preparation | Contained; preserve authoritative M6 integration |
| `23ca836` Synology/Immich progress | Contained; unrelated, do not replay or edit |
| `7ef0b96` preflight/procedure | Contained; preserve as executed release provenance |
| `85d2e46` recovery reporting | Contained; preserve reviewed checkpoint behavior/history |
| `a08114b` deployment evidence | Contained; preserve exact Stage1 hashes, startup-race/recovery and 601-second observation |
| `30f79ea` first local contracts/design | Unique files, conceptually overlaps remote59a7c52/8b46d55; initial trust design superseded by026e5e9. Retain as selector probe, not second canonical harness |
| `026e5e9` trust corrections | Unique; retain independent expected-source pin, request engine binding, filtered eligibility projection and explicit scope denial |
| `1a8fa68` portable conformance | Unique; retain 31 vectors and all applicable tests under explicit probe namespace |

## Resolution of overlapping contracts

Remote `scripts/aster-adaptive` remains the programme's harness, routing experiment
and evidence-ledger implementation. Its M3 negative/retain results, datasets,
M4 lineage, paired evaluation and restore evidence remain unchanged. This merge
does not replace that more advanced work with a selector-only benchmark.

Local `services/aster-adaptive` is an **offline selector conformance probe**.
Its records are not canonical execution/ledger records: tool selection, fixture
execution and measured outcomes mean different things. Both implementations had
used `decision.v1`, `capability.v1` and related names for incompatible shapes.
The probe now uses `selector-probe.*.v1`, with schemas under
`schemas/aster/selector-probe-v1/`. There is no implicit conversion or ingestion
into the harness ledger. Any future bridge requires reviewed field/semantic
mapping and conformance tests, not renaming a schema string.

The probe's source pin, engine binding, eligibility projection and fail-closed
checks remain intact. Namespacing changes catalogue digests; portable vectors
were rebound to the changed catalogue while preserving intentional wrong-digest
negative cases. All 31 vectors pass. Old probe manifests/results remain historical
to commits026e5e9/1a8fa68; do not compare their old paths against the integrated
tree as though they were current manifests. New current results are
[selector-baseline.json](selector-baseline.json) and
[selector-conformance.json](selector-conformance.json), each with exact hashes.

## Validation and limits

- 52 remote harness/evidence tests pass, unchanged code.
- 29 selector-probe tests pass, including 31 portable contract vectors.
- 76 broker tests pass, unchanged integrated authority code.
- 163 Aster tests pass, unchanged runtime/approval source.
- Source manifests for both new result files match the isolated working tree.
- Broker, approval, Aster and existing harness trees are byte-for-byte unchanged
 against `f25df18`; the primary checkout's unrelated dirty files were untouched.

The initial namespace conversion exposed invalid positive-vector registry digests.
Recomputed only those bindings that matched the old valid catalogue; intentional
wrong-registry/policy/engine cases remain failing. This is recorded as integration
feedback rather than weakening conformance expectations.

Tests use the already available local Python environment. No package installation,
model request, infrastructure mutation, real-data collection or automatic promotion.
The optional PydanticAI candidate suite was not rerun because its code and inputs
are unchanged; its historical measured results are preserved without new claims.

## Integration and rollback plan

1. Base the isolated branch on pinned authoritative `f25df18` (done).
2. Merge the three residual local commits without losing either lineage (done).
3. Keep remote M1/M3/M4 and authority files; scope/name the local probe (done).
4. Run the four affected suites and new manifest/conformance checks (done).
5. Commit locally; leave primary main and unrelated changes untouched.
6. Before any separately approved publication, recheck current Forgejo head and
   coordinate with AI-PAM/other active work. Do not force-push or assume this
   pinned baseline is still newest. GitHub receives only Forgejo's mirror.

Rollback requires discarding the unused integration branch/worktree, retaining
history/evidence; no production service or DB rollback is involved. Stage2 remains
undeployed. Future authority changes remain owned by AI-PAM and separately gated.
