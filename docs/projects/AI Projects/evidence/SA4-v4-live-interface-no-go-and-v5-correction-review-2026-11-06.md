# SA4 v4 live interface NO-GO and v5 correction review — 2026-11-06

## Measured result

Jason approved exactly one fresh SA4 distinct-canary repair attempt. Fresh
preflight found the installed v4 hashes exact, the target at the required
drifted digest `a9831e62…4da0`, all v2 transaction paths absent, the whole-host
lease exactly `ready`, and production healthy. Fresh owner and AI-PAM
signatures authenticated plan `e708b2f7…647b`; the six fixed inputs were
staged root-owned, mode 0600 and one-link with 791 seconds of grant validity.

The fixed v4 runner was invoked exactly once. It exited 1 before creating the
ledger, runtime controls, observer exchange, checkpoint or repair:

- first failure phase: `runner-pre-effect-interface-check`;
- failure class: `deterministic-source-interface-defect`;
- failure code: `missing-root-owner-bound-target-id`;
- exact exception: `AttributeError: module 'sa4_root_transaction_owner_v4'
  has no attribute 'BOUND_TARGET_ID'`.

No retry occurred. The canary remained byte-identical at
`a9831e62…4da0`; the one-use ledger, operation lock, emergency stop and
observer exchange remained absent. The empty, root-custodied evidence
directory and exact transaction inputs are retained. The host observer bridge
directory is retained empty. The lease returned exactly `ready`; LXC
104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech, `pvescheduler` and
`pvestatd` remained healthy with zero service restarts.

## Deterministic correction

The failure was not an infrastructure or authority problem. The v3 predecessor
runner deliberately reads `root_owner.BOUND_TARGET_ID`; the v4 owner preserved
the closed phase graph but omitted that public compatibility constant. Existing
unit tests mocked the predecessor execution and therefore did not traverse the
interface read.

The source-only v5 correction is additive and preserves the spent v4 files as
evidence:

- `sa4_root_transaction_owner_v5.py` exposes the fixed target constant and
  retains the complete registry-v2 binding, SHA-256 `a4fd7073…167a`;
- `sa4_fixed_transaction_runner_v5.py` checks that interface before calling
  the real v3 predecessor, SHA-256 `1071e4aa…6b6f`;
- new tests bind the v3 predecessor target to the v5 owner rather than mocking
  that interface away.

The complete SA4 suite passes 286/286. The canonical two-file create-exclusive
inactive-install plan is `134ef9c6…6543`. It invokes no runner or signer and
does not alter retained attempt state, the canary, services, models, routes or
promotion. Installing those two absent files is the next exact operational
gate. Any later repair requires new owner and AI-PAM signatures and a distinct
one-use grant; the failed authority packet is not reusable.
