# SA4 root transaction owner source boundary — 2026-11-05

## Outcome

A source-only root transaction owner now sequences the fixed SA4 components
through one closed state graph:

1. authenticate the exact owner and AI-PAM authority;
2. measure and create one exact checkpoint;
3. recompose the live preflight with fresh runtime controls immediately before
   the effect;
4. claim the one-use ledger entry once;
5. create the final one-effect admission and invoke the fixed atomic owner;
6. produce one independent postcheck receipt and pause for its external proof;
7. either reconcile a passing receipt or perform one fixed rollback, produce a
   rollback receipt and pause for its external proof;
8. terminally reconcile and burn the grant.

The owner has no command runner, transport, signer, retry method, arbitrary
path or model call. Independent signing remains outside the effect owner. Any
exception after a phase starts moves the owner to
`uncertain-manual-reconciliation-required`; it cannot repeat the phase or
finish as success.

## Verification

- ordered success/terminal-burn unit path: pass;
- phase skip and second-effect rejection: pass;
- injected post-claim failure becomes manual uncertainty: pass;
- root-owner focused tests: 3/3 pass;
- complete SA4 suite: 137/137 pass;
- whitespace/error check: pass.

This is source only. It created no authority, signature, claim, checkpoint,
receipt, target mutation, rollback, service action, booking or route.

## Next gate

Replace the hand-sequenced disposable rehearsal with this root owner and prove
both its success and rollback branches end-to-end. Only after that review may
an exact inactive-install upgrade packet be prepared. The first real repair
still requires immediate approval for that exact effect.
