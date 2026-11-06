# SA4 distinct canary v2 proposed registry — 2026-11-06

The next proof target is now source-complete as a proposal without changing the
production registry. It names only
`/var/lib/aster/sa4/canary-adapter-v2.json` in LXC104, with a fixed drifted
initial artifact `a9831e62…4da0` and fixed healthy candidate
`fae178a1…a0c2`. Both are 85-byte inert JSON fixtures. The existing repaired
canary, credentials, network, firewall, model, services and shared
infrastructure are excluded.

The proposed registration reuses the already reviewed generic target-byte,
metadata, consumer-health and rollback programs but lives in a separate
source-only registry. No installed module imports it, and the production
resolver rejects the new target ID. Its owner-review card is canonical at
`6934128f…713`; it explicitly records `owner_decision=pending`, grants no
authority and authorizes no effect.

The complete SA4 suite passes **237/237**. Next is Jason's exact acceptance or
rejection of this proposed inert target. Acceptance would authorize only
promoting the registration into a separately reviewed inactive registry and
preparing a reversible create-only seed installation. It would not authorize
that installation, a repair, signer use, grant, service action, restart, route
or promotion.
