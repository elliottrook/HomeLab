# SA4 one-shot effect controller source — 2026-11-05

The first source correction for the v4 pre-effect NO-GO now keeps the exact
root transaction owner alive for the complete phase graph. It sequences
prepare, one effect attempt, independent observation, proof acceptance,
optional one rollback, independent rollback observation and terminal
reconciliation in one process.

The controller accepts an external observer-signing callback but never a key.
It constructs and validates the fixed canonical observer statement itself,
accepts only one 2048-bit RSA signature shape per observation, and returns a
content-free terminal digest. The success branch requests one signature; the
rollback branch requests exactly two. A signer failure stops before finish,
and there is no retry path.

Four focused tests cover success, rollback, signer failure and input drift.
The complete SA4 suite passes 171/171. This source is not installed and cannot
perform a live repair. The remaining boundary is a fixed, hash-pinned
Proxmox-to-LXC proof transport that implements the callback without exposing
the observer key or accepting arbitrary commands.
