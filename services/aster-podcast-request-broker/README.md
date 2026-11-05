# Aster podcast request broker

This service implements AsterTV v3's owner-approved podcast request queue. It
uses a read-only Audiobookshelf API key for discovery and duplicate checks, and
a separate hash-only AsterTV client token for queue access. It contains no
Audiobookshelf admin credential and has no subscription executor.

The only HTTP routes are:

- `GET /health`
- `POST /v1/search`
- `POST /v1/request`
- `GET /v1/status?request_ref=...`

Deployment is bounded by `SA-M5P-JEN` in `docs/projects/AsterTV-v3.md`.
