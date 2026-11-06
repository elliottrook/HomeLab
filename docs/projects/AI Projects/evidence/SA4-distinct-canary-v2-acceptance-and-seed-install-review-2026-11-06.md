# SA4 distinct canary v2 acceptance and seed-install review — 2026-11-06

Jason accepted the exact proposal card `6934128f…713`. The canonical owner
acceptance record is `53070fd5…1422` and is limited to source registration and
preparing an inactive seed packet. It authorizes no live installation or
repair.

The accepted source registry preserves the complete v1 registration unchanged
and adds only `sa4-lxc104-canary-adapter-v2` at the accepted fixed path. It
binds the owner acceptance digest and remains uninstalled. The reversible
seed packet contains exactly two create-exclusive files: that inactive
registry and the accepted 85-byte drifted inert JSON seed. Both destinations
must be absent; the installed v1 registry, healthy original canary, spent v6
ledger, runtime controls, lease and production health are preconditions.

Postchecks require exact root-owned single-link files, an isolated v2 registry
import, unchanged v1 target resolution, v2 resolution only through the new
registry, no runner/signer/authority/ledger activity, absent runtime state, no
service actions and healthy production. Rollback removes only the exact seed
and registry after-hash files, in that order. A strict canonical result
validator rejects any hash, custody or prohibited-action drift.

The complete SA4 suite passes **245/245**. The packet is source-only and
repair-ineligible. Its next gate is explicit approval for the two-file inactive
seed installation. That gate does not include registry consumption by the v2
runner, authority signing or a repair.
