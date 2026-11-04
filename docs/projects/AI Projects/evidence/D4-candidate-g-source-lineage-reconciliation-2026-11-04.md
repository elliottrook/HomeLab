# D4 candidate-g source-lineage reconciliation — 2026-11-04

The installed response-normalization correction changed the exact runner hash
to `372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352`.
The registered platform workload and 34-pin release manifest already bound that
identity, but the repository's source-freeze candidate manifest and historical
non-admitted workload proposal still named the predecessor runner. The complete
D4 source suite therefore correctly failed its frozen-source validation.

Both source validators and both canonical JSON records now bind the same
corrected runner. No other candidate control, workload budget, packet identity,
result boundary or denied authority changed. The proposal remains non-admitted
and cannot itself schedule or authorize an effect; live admission remains the
separate authoritative Lab Hours booking.

The combined deterministic envelope, candidate, proposal, runner, batch,
quality-freeze, blind-review and reconciliation suite passes 36/36. This is an
offline lineage correction only. It made no booking, model call, service
change, route, tool grant or promotion and did not alter the already scheduled
R8 transaction.
