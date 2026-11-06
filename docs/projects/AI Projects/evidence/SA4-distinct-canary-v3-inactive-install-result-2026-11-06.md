# SA4 distinct-canary v3 inactive-install result — 2026-11-06

## Result

Jason approved the exact two-file inactive installation. Fresh preflight
confirmed both destinations absent, all direct dependencies exact, the
distinct canary at drifted digest `a9831e62…4da0`, v2 transaction/control
state absent and bounded production healthy.

The two reviewed sources were staged, checksum-verified and linked
create-exclusively into LXC 104. Direct reconciliation after the installer
client boundary found both final files exact, root:root, mode 0644, one-link
regular files, with no staging remnants:

- root owner v3: `2b2d0824…9fb0`;
- fixed runner v3: `9c6bfbbe…c9f`.

All seven installed dependency hashes match. Isolated imports pass, production
registry v1 still rejects the distinct target, and registry v2 resolves only
the accepted fixed path. The strict canonical result beside this record passes
the source validator.

## Zero-effect installed-path proof

The final-path runner was then invoked once with one unexpected argument. It
failed closed at the no-argument boundary with exit 1 before opening inputs or
creating state. The distinct canary remained byte-identical at
`a9831e62…4da0`; input, evidence, ledger, operation-lock and emergency-stop
paths remained absent.

The whole-host lease remained exactly `ready`. LXC 104/110/116, Aster Agent,
accepted llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd` were healthy.
No authority, signature, claim, checkpoint, repair, rollback, restart, service
action, route or promotion occurred.

## Next action

Build a fresh release and unsigned-authority boundary for the distinct target,
then validate it offline. The first v2-canary repair remains a separate exact
effect gate and is not scheduled.

