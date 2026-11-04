# SA3 candidate-g guest-failure diagnostic correction — 2026-11-04

## Outcome

The spent `aster-stream-a-sa3-envelope-20261104-1315-r3` transaction remains
`NO_GO` and must not be retried.  Production restoration passed, but the host
adapter reduced the non-zero guest exit to `unclassified guest failure` because
it attempted to decode the complete stderr stream as one JSON document.  Any
transport or systemd line surrounding the wrapper's bounded JSON receipt made
that decode fail.

This milestone corrects the source-only diagnostic path.  It does not install,
activate, schedule, reserve, or invoke candidate-g.

## Correction

- The host adapter scans stderr lines from the end and accepts only the last
  standalone JSON object containing a string `code` of 1–160 characters.
- Invalid UTF-8, malformed JSON, absent codes, and over-length codes remain the
  content-free `unclassified guest failure` result.
- The guest wrapper reports a bounded count and sorted error-class set when a
  result contains model-request errors.  It does not expose prompts, answers,
  case identifiers, or arbitrary exception messages.
- Malformed error rows fail closed as `candidate-g result errors are malformed`.

Source identities:

- `sa3_evidence_envelope_listener_adapter.py`:
  `fecb32cb29b2981aeab769efff7450e93c9853b30f79ca2131acb4015c74600c`
- `aster_llama_sa3_evidence_envelope_wrapper.py`:
  `1d01c8c5bda942ddb42386eb56066c4858bf8032db39c136a4c9efbb933a4fc2`

## Verification

- Focused macOS source suite: **27/27 passed**.
- Direct Proxmox Python proof: **passed**.  The staged source extracted the
  final bounded JSON code from noisy stderr, rejected unclassified stderr, and
  produced the exact sorted error-class summary for two result errors.
- The exact temporary target staging directory was removed after the proof.
- No service, model, lease, booking, timer, or production file was changed.

## Release boundary

The correction is ready for a separately reviewed, reversible inactive install.
A future candidate-g run requires a fresh authoritative Lab Hours booking,
whole-host lease, shared operation lock, installed-hash validation, and all
normal fresh preflight gates.  This card authorizes no retry or promotion.
