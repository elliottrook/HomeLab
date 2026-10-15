# D4 sysadmin evidence type boundary — 2026-10-15

**State:** Offline source and synthetic tests only. No producer, connected
Codex tool, AI-PAM grant, Doctor schema or live service was changed.

The proposed incident contract already restricts planned targets, observation
count, age, producer envelope and fact-field names. Malformed producer values
could still raise ordinary Python type errors rather than the contract's
`InvestigationError`: for example, an array target or numeric evidence ID.
Python also treats `True == 1`, so a boolean producer or persisted-record
schema version could pass the version check. Non-finite JSON fact values could
enter the local record despite JSON's finite-number contract.

The candidate now rejects those cases explicitly. A bad producer field,
observation-plan entry, schema version or non-finite fact yields a controlled
contract rejection before incident state is saved. The 17 focused sysadmin
tests pass, including new malformed-input cases; `git diff --check` passes.
The adjacent Doctor adapter tests pass (5/5). The FastAPI gateway integration
test could not start in either available Mac Python runtime because neither
has `fastapi`; no dependency was installed and no gateway result is claimed.

This is robustness evidence for the offline boundary, not a security review of
free-text summaries or approval to connect an agent. Source-local privacy
projection, independent diagnostic usefulness, M1 identity/permission checks
and a separate deployment gate remain open.
