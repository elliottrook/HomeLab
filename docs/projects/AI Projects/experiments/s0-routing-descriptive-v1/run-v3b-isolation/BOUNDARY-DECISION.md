# V4 boundary decision after V3b

Decision: **GO to accepted-corpus candidate preparation; execution is not authorized**

V2b proved fresh-image bootstrap, a no-vNIC topology, bounded serial export and
clean shutdown. V3 failed before the probe because its canary path conflicted with
the private temporary namespace. The new immutable V3b candidate corrected only
that test-design defect, retained the security and resource controls, and used a
fresh image, VM and run identity.

V3b produced a single digest-bound canonical result. All ten mandatory checks were
true, the guest powered off within the outer bound, no host stop was needed, and
VMs118–121 are stopped. This is sufficient positive evidence to accept the
disposable VM design as the boundary for a separately reviewed S0 corpus
experiment.

Residual risks remain: one successful isolation run does not prove repeatability,
QEMU/systemd isolation is not a formal security proof, and corpus execution adds
new parser, resource and data-handling failure modes. The next candidate must use a
new identity and fresh disk, remain offline and credential-free, pin the exact
accepted corpus and code, preserve fail-closed parsing and lifecycle bounds, and
require a new human approval before execution.

No model, prompt, route, permission, policy or architecture change is promoted by
this decision. It changes only the boundary gate from NO-GO to preparation GO.
