# AsterTV fleet composition authority

This directory is the machine-readable desired-state authority introduced by
the AsterTV Platform Engineering and Design Operations project. It composes an
immutable global release with measured hardware/peripheral profiles and named
overlays. It does not deploy anything.

Canonical manifests use the JSON subset of YAML 1.2. This keeps the requested
`.yaml` contract names while allowing deterministic, dependency-free parsing
with Python's standard library. Secret values, account content and observed
media state are forbidden; `secret_refs` are opaque custody identifiers only.

Compile the fleet and regenerate the committed human/machine outputs:

```sh
python3 services/kodi/astertv-fleet/compile_fleet.py
```

Run the M1 gates:

```sh
python3 -m unittest discover services/kodi/astertv-fleet/tests -v
```

The compiler:

- validates every registry object and reference;
- topologically orders overlay dependencies;
- rejects incompatible releases, undeclared targets and duplicate ownership;
- rejects secret-bearing keys and malformed opaque references;
- emits deterministic per-device desired manifests and a release matrix; and
- keeps Guest as a compiled, non-deployed candidate.

## Payload and bundle gate

Every overlay declares repository-relative `payload_sources`. Compilation
expands directories into an exact, sorted file inventory and records SHA-256,
byte count and path in the desired composition. A source-byte change therefore
changes the device composition hash instead of silently inheriting a hotfix.

`build_release_plans.py --artifact-root services/kodi/dist` verifies the pinned
base release and builds deterministic per-device bundles containing the base,
payload inventory, source bytes and guard contract. Bundles are candidates, not
permission to deploy. An overlay remains fail-closed until its manifest says
`payload_status: complete` with no blockers. Transformer-only overlays must
first materialize and hash their final outputs; external configuration and
mutable/private state must be represented as assertions or exclusions rather
than copied into the bundle.

The composition guard accepts exact payload observations, typed assertions and
required dependency states. `doctor_fleet.py` evaluates only deployed devices
and fails closed on missing, stale, future, malformed or composition-mismatched
observations. Missing, unknown or changed payloads, unavailable required
dependencies, identity mismatch and composition mismatch all produce drift.

Current bundle-build status (2026-11-05): Bedroom is the first composition with
all selected overlays materialized. TV details is emitted as one 12-file tree
whose recovered outputs are bound to the complete exact-hash transformer chain;
Kodi addon enablement and the shared family-manifest component pin remain typed
assertions. News playback is rendered per target from exact accepted
predecessors, with Family advanced to the current bounded-queue revision.
Family media lifecycle is also rendered from its exact checkpoint, while
Intro Skipper remains hash-pinned external Jellyfin state. The Family equipment
bridge packages exact recovery sources and verifies live HA/Agent/OPNsense
state through assertions. Jen's immutable account registry is now materialized
without mutable profiles, authority state or credentials. Bedroom, Family and
Jen are complete, and Guest is an
intentional non-deployed candidate. This status is eligibility evidence, not a
deployment instruction.

Generated composition hashes deliberately exclude observations and timestamps.
They remain stable for identical source manifests. Live state belongs in a
the `observed/` Doctor surface and can never become desired state implicitly.

