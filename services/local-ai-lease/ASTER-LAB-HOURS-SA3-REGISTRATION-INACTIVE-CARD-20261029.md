# SA3 expanded-source quality — third Lab Hours registration

Status: **registered in source; inactive target validation is fail-closed**

This card adds the third fixed root-owned identity
`sa3-expanded-source-quality-v1` to the reservation contract. It is distinct
from both qualification identities and cannot be selected by an arbitrary
command.

## Fixed registration

The registration is implemented in
`scripts/local-ai/lab_hours_workloads.py` and included in the release manifest.
It binds:

- exactly 20 sequential requests;
- 120 seconds per request and a 2,700-second workload deadline;
- a minimum 3,600-second booking with a 900-second restoration reserve;
- the visible packet, packet validator, one-call/no-retry runner and its
  independently reviewed fair scorer only;
- the accepted model/binary/unit baseline already used by Lab Hours; and
- root-owned, bounded result retention with no automatic qualification,
  routing, repair, model change or restart authority.

The answer key and independent-review receipt are not runtime registration
files. The fair scorer is included because the packet validator imports it at
module load; its independent review hash is
`92a4526886b21492995b73c834844a570b7718415abcadce848bcd1da6860bda`.

## Inactive-target validation

`lab_hours_inactive_target.py` validates the exact four file hashes, root
ownership, regular-file/no-symlink custody and absence of a target service or
timer. It also checks local Python import closure so an omitted runtime
dependency cannot pass hash validation silently. This validator has no effect
authority and does not create a booking, schedule or unit.

The reserved runner uses the registered 2,700-second guardian rescue boundary
and fails before any production drain while the SA3 runner transaction is not
installed and independently validated.

The source-only transaction candidate is
`scripts/local-ai/sa3_expanded_quality_transaction.py`. It composes the
existing full-drain controller, checks the pinned packet result for exactly 20
responses and zero retries, writes the complete bounded result only beneath a
root-owned mode-0700 attempt directory as mode-0600, and projects only a
content-free receipt containing the prediction digest. The injected runner
heartbeat is required before and after the workload and is intended to be
called between requests by the fixed runner. Cleanup and the existing restore
postcheck run on success and every failure path; the guardian remains the
owner-loss authority.

The transaction source hash is
`202f99608a44f6d2bdc9fac8f69b2c09ceb84d1b4d143942fb6bb935041965f4`; its
focused transaction and platform boundary suite passes **24/24**.

## Current incompatibility — NO-GO

The source proposal has now been corrected to include the independently
reviewed scorer as a fourth runtime pin. The platform registration reflects
that four-file closure. The remaining incompatibility is operational: the
existing reserved runner has no SA3 full-drain transaction, so the target
remains inactive and the runner fails closed before any production drain until
that transaction is separately implemented and reviewed.

The separate full-drain runner transaction is not admitted by this card. The
current reserved runner still retains `WORKLOAD_RUNNER_UNAVAILABLE`, and the
transaction's default listener target is deliberately inactive. The source
transaction therefore cannot be invoked by a booking or schedule yet.
No booking, schedule, model call, backend change, deployment, restart or
production effect follows from this source registration.
