# D4 evaluation-input envelope boundary — 2026-10-23

## Finding and correction

The fresh investigation executor validated the parsed case bundle and release
manifest, but read both complete files before applying any byte limit. Python's
default JSON decoder also accepted repeated object keys by retaining the last
value. A malformed local input could therefore consume unbounded runner memory
or hide an earlier field before the release and case checks ran.

The executor now reads each input through a 1,048,576-byte envelope before JSON
decoding and rejects repeated keys at every object level. The existing sealed
release digest, case digest, field-shape and label-exclusion checks still run
after this transport boundary.

## Verification and limit

A normal synthetic object passed. A file one byte over the input envelope and
an object with a repeated key were rejected. The complete evaluation unit suite
passed 119/119.

This hardens an offline, separately approved evaluation runner. It does not
read the private holdout, call a model, qualify an investigation, enable
routing, connect a tool or grant authority.
