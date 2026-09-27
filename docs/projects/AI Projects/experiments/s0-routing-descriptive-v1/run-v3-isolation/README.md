# Disposable VM V3 — isolation fixture did not pass

Result: **FAILED / INCONCLUSIVE; NO-GO for accepted-corpus execution**

Jason explicitly approved the exact manifest-bound V3 window. Eleven staged files
matched the frozen release manifest. The release created a 380,928-byte ISO with
SHA-256 `51cd876edbfaaaa0c6d328aced51e4aaaa47995030c5e3e39807adf11b576d2a`
and fresh VM120 `aster-s0-isolation-v1`. Its stopped configuration passed the strict
one-core, 1-GiB, 8-GiB, no-vNIC/no-agent/no-share/no-passthrough gate.

One boot produced a 105,156-byte capture with SHA-256
`11984e6a9cd19351a8d360c20f556d11db3c19c171879780b50c746e9e2ced86`.
The guest showed only loopback and cloud-init reached the reviewed unit, but
`aster-s0-isolation.service` failed. No `ASTER_S0_V1` record was emitted, so the
strict parser returned `incomplete protocol`. The guest powered off without a host
stop; no retry was made. VMs118,119 and120 are stopped. Existing service guests are
running; a concurrent Proxmox backup completed `OK` and explains the temporary
movement of the `backup` lock between the before/after container listings.

The host capture command's zero exit code means the bounded terminal capture
completed. It is not fixture success. None of the ten proposed isolation checks is
proven because there is no authenticated result. The precise service failure is
**UNKNOWN / REQUIRES VERIFICATION** from the stopped disk. The raw capture is kept
only in private temporary and Proxmox evidence storage because it includes noisy
boot output and generated public SSH host-key material; its digest and sanitized
failure lines are retained here.

The V4 boundary decision is NO-GO in
[`BOUNDARY-DECISION.md`](BOUNDARY-DECISION.md). Do not run the accepted corpus,
reboot VM120, retry V3, weaken the unit, or infer that any negative probe passed.
The next useful action is a separately approved read-only forensic inspection of
the stopped disk, followed by a new candidate only if the evidence supports one.

