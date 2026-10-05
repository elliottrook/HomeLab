# Post-LXC100 execution-boundary decision

Date: 2026-09-26

## Decision

**STOP accepted-corpus execution and retire LXC100 as the S0 isolation target.**

Run003 produced the evidence the feasibility series was designed to obtain: the
reviewed systemd namespace combination fails inside LXC100 with `226/NAMESPACE`
before payload readiness. Weakening `PrivateNetwork`, filesystem namespace or
related controls to make the transient unit start would change the security claim,
not fix the experiment. A fourth shared-host attempt is rejected.

## What this does and does not establish

Verified:

- preflight health, resource and DNS checks can run safely on LXC100;
- the exact canary lifecycle and receipt-guarded recovery work;
- the reviewed transient-unit isolation combination is not feasible in this LXC;
- recovery restored the household Docker/Pi-hole host to its baseline.

Not established:

- which individual namespace directive is incompatible;
- that all systemd isolation is impossible in every LXC configuration;
- that the S0 evaluator is incorrect or unsafe in a suitable execution context;
- that accepted-corpus execution, model routing or operational automation is ready.

Finding the minimum directive that starts would optimize for a passing demo while
eroding the reviewed boundary. That investigation has insufficient value on a
shared household host and is explicitly out of scope.

## Replacement boundary

The preferred future target is a **dedicated, disposable Linux VM** with no service
role, no credentials, no secret mounts, no route to household management networks,
and no dependency on GPU or cloud services. The VM should expose only a bounded
artifact input and result export mechanism. The same systemd restrictions must be
tested with invented fixtures before accepted data is admitted.

No existing VM is approved for reuse. VM105 is a stopped inference rollback guest
and remains rejected. Repository evidence warns that configured guest limits are
not a safe spare-capacity budget, so this decision does not claim current placement
capacity. The planned second node may eventually be a cleaner location, but Stream A
must not depend on unbuilt hardware.

## Required evidence before implementation

1. Read-only capacity and storage assessment for a small disposable VM.
2. A reviewed network-deny design, including management-plane separation.
3. Pinned base image provenance and rebuild/retirement procedure.
4. Exact CPU, memory, disk, runtime and output limits.
5. Fixture proof for network, process, filesystem and resource denial.
6. Explicit approval for VM creation and any image acquisition.
7. Separate approval for the eventual accepted-corpus run.

Until these exist, S0 remains at a valid negative feasibility result. Routing
implementation and fixture tests may continue locally; accepted-corpus execution
does not.
