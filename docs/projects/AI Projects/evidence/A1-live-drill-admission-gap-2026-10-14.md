# A1 live drill: remaining provenance and transport gates

Status: **offline source review; no live drill authorized**.

The [disabled helper upgrade](A1-disabled-helper-upgrade-2026-10-14.md)
installed only fixed helper files. It did not create an application lease,
temporary credential, ingress rule, sidecar process or admission identity.

The platform [drill card](../../../../services/local-ai-lease/APPLICATION-B60-DRILL-RUN-CARD.md)
requires a current-cycle Proxmox artifact check, exact LXC110 mirror check,
and Mac `source-destination-exact-subset` receipt bound to task 2 start and
finish. The current `application_b60_drill_entrypoint.py` validates a
root-owned `prelease.json` schema and checks that its `backup_receipt` begins
`application-chain:`. The repository search at platform commit `7b36ce64`
found no producer that derives that JSON and marker from those three fixed
backup sources. The installed helper therefore has a schema check, but
source provenance is **not proven**. A hand-written root JSON could satisfy
the visible fields; its truth would depend on the operator rather than a
repeatable source adapter. This is an architectural inference from source,
not a claim that an unapproved live attempt was made.

Before an effectful drill, the platform owner should pin a producer with
fixed read-only source commands and an owner-only output path; capture each
source's timestamp/hash/identity, check current-cycle ordering and exact
subset equality, then bind the derived digest to the prelease and later
admission receipt. Negative tests should reject fabricated, stale,
wrong-cycle, partial and `tree-present-only` inputs. A positive fixture alone
does not establish a trustworthy backup chain.

The admission CLI is installed, but the required restricted Mini-to-Proxmox
forced-command identity is not part of the approved install packet. Its
live configuration and pinned host-key path remain **REQUIRES VERIFICATION**.
Do not substitute root SSH or a caller-supplied boolean for that identity.
The one-minute heartbeat remains disabled; its ability to revoke a stale
admission has not been exercised in a live recovery drill.

The next approval request should contain one reviewed effect card with the
exact source producer/transport pins, current-cycle backup evidence, protected
rollback checkpoints, bounded key/restart/generation count, and stop
conditions. It must remain separate from approval for the 20-call A1 batch.
