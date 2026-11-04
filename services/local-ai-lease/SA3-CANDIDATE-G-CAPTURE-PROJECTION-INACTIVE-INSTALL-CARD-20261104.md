# SA3 candidate-g capture-projection inactive install card — 2026-11-04

Replace only the host candidate-g adapter and matching release manifest:

- adapter `fecb32cb…c74600c` → `101ce58e…e3c9f`;
- manifest `6fa56d9c…a157f71` → `1d18a86d…d9537`.

Create root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-capture-projection-r1-20261104`
before replacement. Refuse checkpoint existence, baseline/source/custody drift,
non-ready lease, shared state/lock, failed manifest/import/projection proof, or
rollback uncertainty.

Accept installed proof only when all 34 manifest pins load and synthetic inputs
return, respectively, a bounded JSON code, class-only traceback code and
exit-status/channel-byte-count code. Raw text and messages must remain absent.

This inactive effect makes no booking, model call, guest/runtime change or
service restart. It authorizes no candidate run, retry, backend/model change,
blind review, route, tool grant or promotion.
