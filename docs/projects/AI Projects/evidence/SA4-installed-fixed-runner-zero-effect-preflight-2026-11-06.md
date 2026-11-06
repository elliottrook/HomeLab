# SA4 installed fixed-runner zero-effect preflight — 2026-11-06

The installed runner's no-argument boundary was checked through its final
path. An unexpected argument failed closed with exit one before creating any
input/evidence directory, ledger, exchange, lock or emergency stop. Temporary
stdout/stderr captures were removed.

The runner was not admitted into a transaction, no signer or private key ran,
and the canary remains `19b4e02d…df1a`. This closes the installed-path
zero-effect preflight. Next is the final post-runner release packet binding
result `27ceea48…a2bd`, followed by a new exact repair approval.
