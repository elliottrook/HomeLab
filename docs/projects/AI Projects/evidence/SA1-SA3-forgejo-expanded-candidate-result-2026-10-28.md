# SA1–SA3 Forgejo-expanded candidate result — 2026-10-28

## Result

**PRE-RELEASE PASS; NOT DEPLOYED.** The candidate expands the installed
Doctor-led adaptive investigation from three observations to four by adding
the fixed aggregate `forgejo-main/git` producer. It passed **80/80** tests under
LXC104's application Python and then completed one isolated connected run from
temporary candidate files.

The live bounded sequence was:

| Step | Target/kind | Observed state | Decision |
|---|---|---:|---|
| Seed | `homelab-doctor/status` | `fail` | existing sanitized report |
| 1 | `forgejo-main/git` | `ok` | observe, authority/effect none |
| 2 | `aster-gateway/status` | `ok` | observe, authority/effect none |
| 3 | `inference-server/status` | `ok` | observe, authority/effect none |
| 4 | null | n/a | complete, authority/effect none |

The result contained four decisions, three consumed registered observations
and four observations. The accepted model was idle and healthy afterward.

## Defects found and corrections

The repeated daytime candidate runs failed closed and produced concrete fixes:

1. The first temporary source packet omitted the pinned producer fixture. The
   corrected packet included it and passed all target tests.
2. The HTTP test helper sent the Forgejo target with `kind=status`; the boundary
   rejected it because only `kind=git` is registered. The test now emits the
   exact pair.
3. The reconnect view intentionally reports `bounded` at the global fourth
   observation even when the plan is exhausted. The test now preserves that
   established fail-closed contract; terminal completion is separately proven
   by the trusted proposal decision.
4. The model echoed the adjective “fixed” from a model-visible reason, which
   the effect guard correctly treated as a repair claim. Candidate reasons now
   say “registered”; the completed-effect guard remains strict.
5. Independent target/kind enums allowed cross-product output when `git` and
   `status` checks coexisted. The current llama.cpp grammar did not reliably
   support a cross-field `anyOf` correction. The boundary now exposes only the
   next registered pair and the transport rejects requests containing more
   than one remaining check. The model still chooses observe, complete or
   escalate; it cannot reorder or synthesize a target/kind pair.
6. Blank and oversized hypothesis output now receives a fixed transport error
   before journaling; no fallback hypothesis is invented and there is no
   in-run retry.

## Exact candidate and postchecks

- Final temporary packet SHA-256:
  `9abddbaa152da560fba444b687b044c83de250fbe905d8c56b18993b12d3bdd8`.
- Aster Agent remained active on PID `26953`, restart count `0` and exact
  `/health` status `ok`.
- Accepted llama.cpp/SYCL remained active on PID `61089`, restart count `0`.
- Local AI lease returned exactly `ready`.
- Temporary candidate source and state were removed.

The old candidate-E independent-review receipt remains immutable historical
evidence for the installed three-source version. This expanded candidate has
changed source bytes and therefore requires its own exact review and rollback
release packet before one separately approved Aster Agent restart.
