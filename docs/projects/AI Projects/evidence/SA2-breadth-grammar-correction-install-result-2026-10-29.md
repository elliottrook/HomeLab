# SA2 breadth grammar correction install result — 2026-10-29

## Outcome

**PASS.** Jason approved the grammar-based boundary candidate at local commit
`175607e2`. Stream A preserved the installed predecessor in
`/var/lib/aster/sa2-boundary-pre-175607e2-20261029`, installed only
`/opt/aster-agent/sysadmin_proposal_boundary.py` at SHA-256
`a904a1296bf27bb13c0c2a475f3c168f65dde1c53bfcd9e8d4dacacb67e17652`,
and restarted only Aster Agent.

The installed four-source investigation then completed:

| Step | Source | State | Decision |
|---|---|---|---|
| 1 | NetBox network inventory | `ok` | observe gateway configuration |
| 2 | gateway public configuration identity | `ok` | observe backup catalogue |
| 3 | typed backup-protection catalogue | `fail` | observe sanitized agent log |
| 4 | sanitized priority-0–3 log aggregate | `ok` | complete bounded diagnosis |

The journal contains four decisions and three consumed follow-ups. Every step
has authority `none` and effect `none`. The terminal hypothesis identifies the
backup-protection failure as source-specific and does not claim or request a
repair.

## Production postchecks

- all four installed adapter hashes match the reviewed release;
- the serialized Doctor publisher, log publisher and systemd units retain their
  reviewed hashes;
- the log-report timer remains enabled and active;
- Aster Agent is active at PID `33813` with restart count zero after the
  approved restart;
- accepted llama.cpp/SYCL remains active at PID `63414` with restart count zero
  and health `ok`;
- the whole-host lease is exactly `ready`;
- temporary connected-test files and state were removed;
- both root-owned rollback checkpoints remain available.

This completes the SA2 evidence-breadth deployment and connected gate. It does
not grant repair authority or generic shell access, enable automatic routing,
promote a model, or change the Companion. The next D4 task is representative
answer-quality evidence over the expanded source set.

