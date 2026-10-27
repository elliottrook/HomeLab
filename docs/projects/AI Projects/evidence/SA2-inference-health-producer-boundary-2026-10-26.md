# SA2 inference-health producer boundary — 2026-10-26

## Result

**SOURCE-ONLY PASS.** The SA2 registry now has a second exact pair:
`inference-server/status`. It makes one unauthenticated `GET /health` to the
fixed accepted llama endpoint at `192.168.70.12:11435`, with a three-second
timeout and a 1024-byte response limit. It sends no prompt, inference request,
credential or caller data.

Only HTTP 200 and the exact unique-key JSON object `{"status":"ok"}` maps to
`ok`. Connection errors, HTTP failures, duplicate keys, wrong state, wrong
shape and oversized responses map to a bounded `unavailable` observation.
There is no caller-supplied URL, host, port, path, target or producer.

The owner-authenticated incident candidate now preregisters this fixed check
after Doctor and gateway status. SA1 still selects the next evidence pair and
the existing journal remains the sole authorization for one observation.

## Validation

- dependency-free incident/selector/producer suite: **37/37** with
  `ResourceWarning` fatal;
- LXC104 production-dependency producer and route suite: **12/12**;
- one bounded live health observation returned target `inference-server`, kind
  `status`, state `ok`, and only the fixed service/endpoint facts;
- temporary target files were removed;
- Aster Agent remained active at PID `17132`, `NRestarts=0`;
- accepted `aster-llama.service` remained active at PID `48161`,
  `NRestarts=0`.

No production file, service, model, incident database, authority or route was
changed. Deployment remains a separate Aster Agent restart transaction.
