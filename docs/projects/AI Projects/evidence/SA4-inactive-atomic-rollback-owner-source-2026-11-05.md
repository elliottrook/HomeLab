# SA4 inactive atomic rollback owner source — 2026-11-05

The one-shot rollback owner is now source-complete with an intentionally
`unconfigured` host binding. It accepts no arbitrary path or replacement
bytes. It requires an authenticated independent postcheck receipt that reports
a failed or uncertain outcome and cross-binds that receipt to the compiled
target, observer-pending effect terminal, original plan and retained exclusive
checkpoint.

The owner reopens the checkpoint without following links, requires the exact
root-owned mode-0600 single-link file and original precondition digest, and
restores it through the target's compiled same-filesystem temporary path. It
fsyncs the replacement and parent directory, retains the checkpoint, removes
an uncommitted temporary file on failure and emits a content-free one-effect,
zero-retry rollback terminal record. It cannot treat its own assertion as an
independent rollback receipt.

Three disposable tests prove one authenticated failed-postcheck restoration,
the inactive committed host binding, and refusal of both a passing receipt and
a changed checkpoint. The full SA4 suite passes **115/115**.

Nothing was installed or invoked on LXC 104. No signer, claim, live checkpoint,
repair or rollback effect ran. Next is the independent rollback receipt
producer and a joined disposable success-plus-failure transaction rehearsal.
