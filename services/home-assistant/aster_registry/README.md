# Aster Home Assistant registry exporter candidate

This custom integration is disabled by default. It registers no Home Assistant
service, action, entity, HTTP route or credential. When an explicit YAML block
is present, it looks up only configured registry IDs, maps them to reviewed
non-sensitive aliases and atomically writes mode-0600 JSON to
`/share/aster-registry/latest.json` initially, on relevant state changes and
every five minutes.

The allowed output domains are lights/switches, timers and media players. Raw
friendly names, attributes, device data, unrelated entities and credentials are
never included. Missing, unknown and unavailable objects fail closed from the
snapshot. The output path is fixed to prevent configuration from turning the
integration into a general file writer.

This directory is an offline deployment candidate. Do not install it or add a
configuration block until VM 103 is snapshotted, the exact alias map is reviewed,
Home Assistant configuration validation passes, and a rollback/removal plan is
recorded. An empty alias map proves packaging only and is not real-registry
acceptance evidence.
