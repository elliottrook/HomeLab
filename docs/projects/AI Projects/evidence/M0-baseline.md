# M0 — programme start baseline

Date: 2026-09-25. Scope: local documentation consolidation, read-only verification and synthetic security tests. Owner: Jason. Authorization: user's explicit Stream A start instruction in this session.

## Verified baseline

- Read-only direct SSH to Proxmox queried Forgejo guest 108's repository ref: main is `e50b670b906f397e1e70b6d51cf07e88235ac5c5`.
- Local checkout was fast-forwarded from `586457f` to that existing cached ref. No fetch, remote mutation or push was used. Platform approval permitted local Git metadata writing.
- Pre-existing changes in `.claude/settings.json`, `apps/AsterCompanion/build-app.sh`, `docs/projects/TrueNAS-DIY-SAS-Expansion.md` and untracked `docs/projects/Mac-Remote-Administration.md` were preserved.
- Aster, broker, approval and Forgejo gateway services on 104 returned active. Inference on 110, speech on 116 and OpenBao on 117 returned active. These are service snapshots, not end-to-end availability proof.
- Live broker core SHA-256 remains `c8f95571ab5b7be1783fe54394047a8d5c40d9cc9121ffcbdc7ad1af99a87cb1`; transport remains `a45b2ff47fce65dd6c16a204979f00a9636fde4d82b799be14b867a91bf152af`, matching the assessment observations.

## Local validation and M1 start

Existing suite before adding regressions:

```text
python3 -m unittest discover -s ops/credential-broker -p 'test_*.py'
Ran 36 tests
OK
```

Added two synthetic required-denial regression tests in `test_adaptive_foundation_regressions.py`, using in-memory SQLite and transport dispatch with no production connections. They assert that another authenticated agent cannot consume the owner's request and that a Yellow approval cannot survive demotion to probation.

Both are deliberately marked expected failures while the baseline violates those invariants. They are open M1 blockers, not passed security checks. Once corrected, remove the markers alongside the fixes. Existing success-path tests must remain passing. A future unexpected success fails the suite, forcing the evidence/marker to be reconciled.

Validation after adding regressions: **38 tests; 36 pass, 2 expected failures**. Markdown local-link validation covered 15 new/moved/index documents with zero missing local targets. All five moves retain substantive historical content and their predecessor links. This verifies project start and reproduces the blockers; it does not verify a fix.

No production corrective deployment, provider call, dependency installation or collection of personal interactions occurred. No new resource allocation is required for these in-memory tests. Current serving version/headroom and full recovery/approver/concurrency gates remain the unknowns listed in the assessment; M0 completion does not assert they are resolved.

## Risk and rollback

Documentation moves preserve substantive content and Git history. Link repairs are bounded to affected references. Reverting this local milestone restores prior paths; no production rollback is needed. Security probes are disposable local fixtures. Pending remote publication does not affect production recovery or operation.

## Resume

M1: fix originating-agent binding and consume-time policy/demotion checks locally; test expiry, revocation, concurrent consumption, policy changes, restart and explicit approver entitlement. Do not broaden agent access or mark M1 complete until all gates and a bounded deployment validation pass. No additional project-level confirmation is needed for routine authorized local work. Remote pushes still require their own immediate confirmation under AGENTS.md.
