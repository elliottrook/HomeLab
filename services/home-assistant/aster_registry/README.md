# Aster Home Assistant registry exporter candidate

This custom integration is disabled by default. It registers no Home Assistant
service, action, entity, HTTP route or credential. When an explicit YAML block
is present, it looks up only configured registry IDs, maps them to reviewed
non-sensitive aliases and atomically writes mode-0600 JSON to
`/share/aster-registry/latest.json` initially, on relevant state changes and
every five minutes.

The allowed output domains are lights/switches, timers, media players and
explicitly reviewed temperature sensors. The v2 contract additionally emits
only on/off for reviewed lights and finite, bounded numeric temperature values
with recognized units (°C or °F). It does not emit raw friendly names,
attributes, unrelated entities, security state, presence, camera data or
credentials. Missing, unknown, unavailable or out-of-range values fail closed.
The output path is fixed to prevent configuration from turning the integration
into a general file writer.

This directory is an offline deployment candidate. Do not install it or add a
configuration block until VM 103 is snapshotted, the exact alias map is reviewed,
Home Assistant configuration validation passes, and a rollback/removal plan is
recorded. An empty alias map proves packaging only and is not real-registry
acceptance evidence.

The current offline review candidate is documented in
[`REGISTRY-REVIEW.md`](REGISTRY-REVIEW.md) and
[`configuration.reviewed.example.yaml`](configuration.reviewed.example.yaml).
It contains the laundry light plus hall and outside temperature IDs selected
for the Home Hub pilot. All three were confirmed present and enabled in the
live entity registry read-only; their current state and units remain unverified.
This is not deployment authorization.
