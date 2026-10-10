# Adaptive integration checkpoint — 2026-09-26

Jason requested push and continuation. Local source-pin work through `69c2a7e`
was reconciled with Forgejo `616a5af` before publication, preserving newer AI-PAM,
labeling, storage and B60 records. Only the programme status header conflicted;
the resolution preserves Stage1 deployed and Stage2/M4 gates open. No external
service, collector, label intake or deployment was changed in this integration.

The upstream Aster source changed in `_chunk_bonus` and `_rank_knowledge` to improve
AI-PAM knowledge retrieval. The two offline definitions still pinned the older full
source and correctly denied it. Explicit review compared all eight extracted
functions/constants (including chat) by AST; they are unchanged. Both definitions
were deliberately revised to the reviewed full-source hash, recorded in
[source revision evidence](M2-source-pin/retrieval-revision.json). This is an offline
experiment revision, not an automatic accept-current-source mechanism.

The first comparison helper omitted annotated assignments and stopped before
updating either pin. Consequently, source-dependent tests initially failed closed.
After fixing the helper to handle both assignment forms, exact selected-node
comparison passed, pins were revised and all required tests passed:

| Suite | Passing tests |
|---|---:|
| Adaptive harness, evidence and non-collecting label tooling | 102 |
| Separate selector profile | 29 |
| Broker and gateway | 82 |
| Aster application | 170 |

The saved M4 export still reconstructs 164 events and its original head
`sha256:59fa02fe1a196ba123c447d4e773bd9404290970f4446113c8dd61b1b12cc7c9`.
No historical result or manifest was rewritten. This replay is consistency evidence,
not independent human approval or checkpoint custody. The existing Starlette/httpx
deprecation warning remains; no dependency changes were needed.

## Continuation boundary

Newer authoritative work already supplies the selector profile namespace, M4 review
packet, approved S0 protocol design and implementation-only empty forms/fixture
validator. Preserve these instead of building duplicate tools. AI-PAM graduation is
recorded by its owning project; this does not automatically close Aster Stage2's
identity/assurance trust gate.

The next M3 step requires explicit collection and durable sanitized S0 retention
authorization under the existing protocol; no actual cases or human labels were
collected. M4's concrete review packet still needs human judgment and accepted
checkpoint custody outside the writer's control. Stage2 still needs real-session
assurance provenance and the process-trust decision. Do not represent more synthetic
runs as satisfying these gates. Deployment, provider-flow changes and connected
pilot activity remain outside this integration. The next turn should consult the
latest authoritative project/approval records before deciding which gate can proceed.

Publication is requested for this reconciled checkpoint. Verify Forgejo's accepted
commit and GitHub's automatic mirror after pushing; do not push GitHub directly.
