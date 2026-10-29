# SA3 expanded quality dormant installation result — 2026-10-29

Status: **PASS — installed dormant; registration and execution remain absent**

Jason authorized the exact `root-v3` transaction after two earlier candidates
failed closed and rolled back. The installed candidate is platform commit
`6bf0fa5c`, packet SHA-256
`27cbdf5dde3e9b451e33fc29ce575de0cc320dbcd6ebe3089742818627c2ed14`
and deterministic archive SHA-256
`601cbddf6edf6d52d5f2fa4b822e1f705c2d7747b2925a0ff0f2aa05c3f7eac7`.
The installer returned `state=staged-candidate`, `host_files=2`,
`guest_files=5`, `effects=not-attempted` and retained both checkpoints.

## Installed dormant targets

Proxmox contains the two root-owned mode-0644 modules at their reviewed hashes:

- `sa3_expanded_quality_transaction.py` — `0706912279bcb4a511633cfb22f19e691eed94f4aa79e07bdc332f87d0dbbc70`;
- `sa3_listener_adapter.py` — `a6387092f04a8fa8cc35254ce19c9a479cd0177b2fd53caae40ee6012c38f917`.

LXC110 contains the root-owned mode-0755 directory chain plus four mode-0644
runtime files and one mode-0750 wrapper at their reviewed hashes:

- packet — `ed75836af74401709a74333a96d0a22629b23e389e5262bbc365ab6aed018d23`;
- packet builder — `b9011bef592421b6e6c28ec830b17f1296409daa30fd4f508d913ba35c104657`;
- runner — `39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351`;
- fair scorer — `92a4526886b21492995b73c834844a570b7718415abcadce848bcd1da6860bda`;
- wrapper — `27949ff1ba37f825de8d3c4aaeaf6388b9535e72d0063e46eac0e491a6604303`.

Target imports passed from both Proxmox and LXC110. The independent guest
import command was initially malformed by operator shell quoting and produced
no target change; the corrected read-only invocation passed immediately.

## Boundaries and health

The SA3 identity remains absent from the live runner and release manifest.
Both proposed host units and both proposed guest units are absent. Answer keys
and independent-review material are absent. No booking, lease, operation lock,
model request, production drain, service/timer change or restart occurred.

LXC104, LXC110 and LXC116 remain running. Aster Agent, accepted llama.cpp,
Aster Speech, `pvescheduler` and `pvestatd` are active, and no lease state is
present. The root-only incoming archive, extracted stage and host/guest
checkpoints remain retained for the registration review and rollback window.

The next gate is a distinct, reviewed registration change. It must register
only this hash-pinned workload while preserving fail-closed reservation,
whole-host lease and shared-lock enforcement. Installation does not authorize a
booking, model execution or automatic schedule.
