# D4 local-service response-size boundary — 2026-10-23

## Finding and correction

The fresh investigation executor used fixed local endpoints, timeouts and a
sanitizing response projection, but read each HTTP response without a byte
limit before decoding JSON. A faulty local inference service could therefore
consume unbounded runner memory before the private evidence boundary applied.

The executor now reads at most 1,048,576 bytes plus one detection byte for
health, metrics and completion responses. An oversized response is rejected
before text/JSON parsing and before any finished journal event.

## Verification and limit

A small synthetic response passed and a response one byte over the limit was
rejected. The complete eval unit suite passed 118/118.

This hardens an offline, separately approved evaluation runner. It does not
call a model now, change the production inference service, qualify an answer,
enable routing or grant a tool.
