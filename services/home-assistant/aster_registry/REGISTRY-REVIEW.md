# Aster registry review candidate

Status: **prepared offline; not deployed**

This review candidate is intentionally limited to the one alias recorded in
the Home Assistant operational reference as of 2026-10-10:

| Group | Home Assistant ID | Aster alias | Review status |
| --- | --- | --- | --- |
| Entity | `light.laundry_laundry_main_lights` | `laundry lights` | Documented as reviewed; recheck against the live registry before deployment |

Rooms, timers and media providers are empty. No entity IDs are being invented
for the Aster Home mockup, and no raw friendly names, attributes, device data,
security state, presence, camera data or credentials are exported.

## Deployment gate

This file and `configuration.reviewed.example.yaml` are repository-owned
candidates only. Deployment remains blocked until all of the following are
recorded in the project evidence:

1. Create or verify the VM 103 recovery checkpoint, without overwriting the
   documented last-known-good path.
2. Read the live Home Assistant entity and area registries through a
   non-secret, read-only query and confirm the exact alias map.
3. Confirm that the selected IDs are still registered, permitted domains and
   available; unknown, missing and unavailable objects must produce no output.
4. Copy the reviewed integration and YAML block into HA only under an explicit
   deployment authorization, then run `ha core check` before a Core restart.
5. Validate `/share/aster-registry/latest.json` is mode `0600`, contains only
   the reviewed aliases, and updates on the documented schedule/state change.
6. Record the rollback checkpoint and the file-level rollback procedure before
   accepting the result.

The candidate does not authorize a Home Assistant change, a VM snapshot, a
restart, or a live registry read that would expose secrets. It is suitable for
local contract tests and design review only.

## Aster Home limitation

The laundry-only registry is sufficient to validate packaging and a narrow
read-only light tile, but it cannot yet populate the Home Hub mockup's rooms,
climate, security, air-quality, routines or media cards. Those require a
separately reviewed source contract and should not be filled with guessed IDs.
