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

Generated composition hashes deliberately exclude observations and timestamps.
They remain stable for identical source manifests. Live state belongs in a
future `observed/` Doctor surface and can never become desired state implicitly.

