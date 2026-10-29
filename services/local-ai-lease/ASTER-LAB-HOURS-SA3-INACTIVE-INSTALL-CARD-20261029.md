# SA3 Lab Hours — inactive Proxmox/LXC110 installation card

Status: **source-only candidate; installation and activation are not authorized**

Packet:
`ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json`

Packet SHA-256: `e4634c7724b8ac8c6b50689285a56f739ea16486f9fd3370f4b47e717ff36e6e`.

The packet is bound to platform commit `8dc6eac5` and Stream A source commit
`434c5aedddd59665c7e2e8961196b81310e02765`. It stages the reviewed SA3
transaction boundary only. `WORKLOAD_RUNNER_UNAVAILABLE` remains present, and
all services, timers, bookings, leases, model calls, production drains,
restarts and remote pushes remain inactive.

## Exact target set

On Proxmox, the packet replaces only these four root-owned `0644` files under
`/usr/local/libexec/local-ai-lease/full-inference-pilot/`:

| File | SHA-256 |
|---|---|
| `sa3_expanded_quality_transaction.py` | `0706912279bcb4a511633cfb22f19e691eed94f4aa79e07bdc332f87d0dbbc70` |
| `sa3_listener_adapter.py` | `a6387092f04a8fa8cc35254ce19c9a479cd0177b2fd53caae40ee6012c38f917` |
| `lab_hours_release_manifest.json` | `2e493d2828c76ec40a5d57be7ef3e0c81588e091eac6b49010a6b21191e1dca6` |
| `aster_llama_sa3_guest_wrapper.py` | `27949ff1ba37f825de8d3c4aaeaf6388b9535e72d0063e46eac0e491a6604303` |

The other sixteen manifest entries are required existing root-owned `0644`,
one-link pins and are re-read before and after staging; they are not replaced
by this packet. The exact prerequisite hashes are in the JSON packet.

In LXC110, stage exactly four root-owned `0644` runtime files under
`/usr/local/libexec/local-ai-lease/full-inference-pilot/`, plus the same wrapper
content as root-owned `/usr/local/sbin/aster-llama-lab-sa3` mode `0750`:

- visible packet `sa3-expanded-source-quality-v1.json` —
  `ed75836af74401709a74333a96d0a22629b23e389e5262bbc365ab6aed018d23`;
- `sa3_expanded_quality_packet.py` —
  `b9011bef592421b6e6c28ec830b17f1296409daa30fd4f508d913ba35c104657`;
- `sa3_expanded_quality_runner.py` —
  `39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351`;
- `sa3_fair_scorer.py` —
  `92a4526886b21492995b73c834844a570b7718415abcadce848bcd1da6860bda`;
- wrapper — `27949ff1ba37f825de8d3c4aaeaf6388b9535e72d0063e46eac0e491a6604303`.

Answer keys and independent-review material must be absent from the guest
runtime directory. No SA3 service or timer may exist in either target.

## Checkpointed transaction

Before any replacement, a separately authorized installer must create fresh
root-only checkpoints at:

- Proxmox: `/var/lib/local-ai-lab/checkpoints/sa3-inactive-install-8dc6eac5`;
- LXC110: `/var/lib/local-ai-lab/checkpoints/sa3-inactive-install-8dc6eac5`.

Each checkpoint records exact prior bytes, owner, mode, regular-file type and
link count for every target. An absent target is recorded as absent. An
unexpected, substituted, symlinked, weakly owned or weakly permissioned target
fails closed before any write. Installation uses only atomic root-owned writes
from the packet and never creates a unit, timer, symlink alias or live entry
point beyond the named wrapper.

## Synthetic validation and rollback

The packet’s import, custody and target-Linux synthetic checks must pass from a
clean source archive with bytecode disabled. The fixed transaction is
`scripts/local-ai/sa3_inactive_install.py`; it is the only installer described
by this card, has a source-only default, and accepts no caller command or
target. Its SHA-256 is
`7356dff11013ec344186871eece8d040871e39e90e872f3da05e7fd50d691299`.
The local source proof is
`scripts/local-ai/test_sa3_inactive_install_packet.py`, SHA-256
`39c5403b0712279e00918b7b1fca1687af585b2a503d2dd6708407c896923e08`, plus
`scripts/local-ai/test_sa3_inactive_install.py` (SHA-256
`13a1c0aaa7354abcbaeef4639b2cf1c501236833dd6e486f9e5a8e892aff9db1`); together they verify all nine
staged payload hashes, target modes/link counts, isolated host and guest
imports, automatic dual rollback, rollback-uncertainty retention and absence
of all four service/timer paths. The combined focused suite passes **56/56**
(the prior platform suite was 46/46).

If staging or postcheck fails, restore only the corresponding checkpointed
targets, remove only paths proven absent before staging, and rerun the custody
and import postcheck. If any state is uncertain, retain the checkpoint and
failure evidence and stop for operator reconciliation; do not retry or delete
uncertain state.

This card does not authorize a Lab Hours window check or booking because it has
no model, GPU, lease, schedule or production effect. A later live installation
requires separate authorization and must still preserve the existing
`WORKLOAD_RUNNER_UNAVAILABLE` fail-closed gate.
