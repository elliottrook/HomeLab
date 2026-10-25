# Stream A prepare-only recovery exercise pass — 2026-10-25

## Decision

The one approved exercise under platform card `7f4dd420`, card SHA-256
`d01d907b0b5bc63bb9ba88d138e145f28366da1bd01f9796cb8810220ab278f2`,
**passed**. This closes the receipt-free pre-effect healthy-owner and
owner-loss recovery proof. It does not arm F6, qualify F2–F5, stop a consumer,
authorize a workload or promote D4/M3.

## Measured result

- lease: `exercise-20261025-1792969326-303bb48b`, generation `1`;
- final status: `complete`;
- healthy decision/effects: `lease-healthy` / `not-attempted`;
- recovery decision/effects: `owner-absent` / `recovered`;
- nested prepared recovery: `cancelled-prepared`;
- consumer commands: `0`;
- F2 unchanged: `true`;
- F6 unchanged: `true`;
- prestate digest:
  `9736b3bc454636f1937a1738f3db10c054968fbc03f54afc11972e3ed290f4cc`;
- command digest:
  `d614cd6b15af54abaa522bd0a185910fe0556213134e586e0647dba750142d30`.

The runner used the fixed transient owner, wrote one heartbeat, proved the
healthy watchdog path inert, stopped only that transient owner and recovered
the still-prepared lease. It made no completion request or model call and did
not invoke quiescence, workload start, outcome or a consumer systemd command.

## Independent postcheck

The durable lease, lease lock, operation lock, identity, owner intent,
heartbeat, watchdog status, restore intent and exercise intent were absent.
The whole-host lease returned `ready`. F6 services remained inactive and its
timers disabled. Aster Agent, accepted llama, Speech, both News timers,
`pvescheduler` and `pvestatd` were active. The October 26 F2 timers remained
scheduled at 01:15 and 01:20 PDT.

The root-owned mode-0600 receipt is
`exercise-20261025-1792969326-303bb48b.json`, 6,935 bytes, SHA-256
`d5cad1d3627da55ccb3ae58318105a05791aa653ac77a26984897ef2e060be13`.
No private prompt, model answer, credential or recovery share was read or
recorded in this Stream A evidence.

The one-attempt approval is consumed. The next live evaluation gate remains
separate: fresh F2–F5 evidence, an exact effectful recovery/activation card and
approval are required before consumer isolation or the already staged D4/M3
workloads can run.
