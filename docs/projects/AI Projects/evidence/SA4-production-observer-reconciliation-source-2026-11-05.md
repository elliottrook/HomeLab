# SA4 production observer/reconciliation source — 2026-11-05

The independent postcheck/rollback receipt validator and terminal ledger
reconciler still resolved only the synthetic schema fixture. Both now resolve
the compiled production registry first and retain fixture fallback solely for
source tests. This closes the next deterministic blocker to a full disposable
transaction rehearsal without accepting an effect outcome.

The observer continues to require the exact accepted observer public key,
fixed postcheck program hashes, canonical signed receipts, bounded timestamps
and zero maximum effects. The reconciler still burns every claimed synthetic
grant as failed or uncertain and never accepts its own repair outcome. New
tests require the production canary to resolve to `lxc104` before fixture
fallback.

The new source hashes are `a37a4926…c3789` for the independent observer and
`9e1caa98…242dd` for the reconciler. Dependent source manifests were updated.
The full SA4 suite passes **105/105**.

No source is installed and no observer, receipt, ledger claim, rollback or
repair effect ran. Next is an inactive observer signer/receipt producer and
rollback owner, then the complete disposable transaction rehearsal.

