# M1/D4 fixed Doctor capability — source candidate

> Decision: **OFFLINE PASS; NO CALLER, BROKER GRANT OR GATEWAY DEPLOYED**

The first post-M1 connected-tool candidate is deliberately smaller than the
existing `lab.doctor.latest` gateway. That gateway may return operator-written
check summaries, so its read-only status does not make it suitable for model
egress. The new candidate accepts one exact empty request and projects only the
already-registered structured Doctor check `aster.agent_inference`.

## Frozen source

- candidate: `services/aster-agent/fixed_doctor_capability.py`
- SHA-256:
  `7c0fd1bcc3404661052627ec7d2fa04e811149f43fb3ea23bc27edf57bb5fb3b`
- tests: `services/aster-agent/test_fixed_doctor_capability.py`
- SHA-256:
  `da5bbc6a2cbdc81a8afb0190c0eedea32928b25df527268c910cac0dd968fb2c`
- focused result: **5/5 passed**
- combined fixed-capability, structured-adapter, model-projection and incident
  contract result: **25/25 passed**

## Contract

The only accepted request is:

```json
{"method":"doctor.aster-inference.latest","arguments":{}}
```

The response contains schema, capability name, source, typed state,
observation time, age and either the fixed check ID or an empty unavailable
fact object. Human summaries, IP addresses, commands, report digests and
arbitrary fact fields cannot cross the boundary. Unknown IDs, stale or future
records, mismatched report digests/runs, extra fields, unsafe permissions and
symlinks all abstain as `unavailable`. The candidate cannot run Doctor, select
a target, execute a command or propose a repair.

## Remaining admission gates

This source composes existing reviewed readers; it is not a live gateway.
Before any model receives it, a later card must freeze the two producer paths
and owner UID, prove the source-owned schema-2 sidecar exists in production,
create a distinct least-privilege Unix caller, register only
`diagnostic.aster-inference.latest`, bind a broker-private socket peer, and
compare held-out diagnostic answers with the existing deterministic Aster
path. A useful answer may say only that the registered Aster inference check
passed, warned, failed or was unavailable at the stated observation time. It
may not infer a cause or repair.

No service, broker database, grant, report, model context or live system was
changed by this candidate.
