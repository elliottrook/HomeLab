# Aster registry review candidate

Status: **prepared offline; not deployed**

Jason selected a three-entity, read-only Home Hub pilot on 2026-10-14. A
read-only query of VM 103's live entity registry confirmed that all three IDs
exist and are enabled; their current state, units and reliability have not
yet been accepted:

| Group | Home Assistant ID | Aster alias | Review status |
| --- | --- | --- | --- |
| Entity | `light.laundry_laundry_main_lights` | `laundry lights` | Documented as reviewed; recheck against the live registry before deployment |
| Temperature | `sensor.hall_hall_sensor_temperature` | `hall temperature` | Present/enabled in live registry; state and unit unverified |
| Temperature | `sensor.outside_outdoor_sensor_temperature` | `outside temperature` | Present/enabled in live registry; state and unit unverified |

Rooms, timers and media providers are empty. No entity IDs are being invented
for the Aster Home mockup, and no raw friendly names, attributes, device data,
security state, presence, camera data or credentials are exported.
The proposed v2 contract exports only on/off for the reviewed light and a
finite, bounded numeric temperature with an explicitly recognized Celsius or
Fahrenheit unit for each reviewed sensor. Unavailable or unexpected values
disappear. Neither config nor code has been copied into HA.

## Deployment gate

This file and `configuration.reviewed.example.yaml` are repository-owned
candidates only. Deployment remains blocked until all of the following are
recorded in the project evidence:

1. Create or verify the VM 103 recovery checkpoint, without overwriting the
   documented last-known-good path.
2. Read the live Home Assistant entity and area registries through a
   non-secret, read-only query and confirm the exact alias map.
3. Confirm that the selected IDs are still registered, permitted domains and
   available; unknown, missing and unavailable objects must produce no value.
   Verify sensor units using a source-local, schema-restricted query; do not
   export raw attributes or a full state dump.
4. Copy the reviewed integration and YAML block into HA only under an explicit
   deployment authorization, then run `ha core check` before a Core restart.
5. Validate `/share/aster-registry/latest.json` is mode `0600`, contains only
   the reviewed aliases, and updates on the documented schedule/state change.
6. Record the rollback checkpoint and the file-level rollback procedure before
   accepting the result.

The candidate does not authorize a Home Assistant change, a VM snapshot or a
restart. It is suitable for local contract tests and design review only.

## Aster Home limitation

The selected values can test a light tile and two comfort readouts, but cannot
populate the Home Hub mockup's rooms, security, air-quality, routines or media
cards. Those require a separately reviewed source contract and should not be
filled with guessed IDs. A protected read-only delivery path from the HA file
to Kodi is also still required.
