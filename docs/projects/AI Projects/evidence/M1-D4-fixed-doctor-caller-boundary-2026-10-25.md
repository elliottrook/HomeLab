# M1/D4 fixed Doctor caller boundary — source candidate

**Date:** 2026-10-25  
**Status:** source-only; no identity, service, broker grant, gateway, model route or schedule deployed  
**Producer predecessor:** `89f18172`

## Boundary

The proposed path uses two narrowly separated local services:

1. `aster-fixed-doctor-caller` runs as new UID `aster-doctor-caller`. It accepts
   one request from the kernel-identified Aster UID:
   `{"method":"doctor.aster-inference.latest","arguments":{}}`. It connects
   to AI-PAM as its own Unix UID, creates one 30-second Green request with an
   empty payload, consumes it once, and validates every returned field before
   returning it to Aster.
2. `aster-fixed-doctor-gateway` is broker-private. It accepts only the
   kernel-identified `hlabroker` UID, reads the root-owned aggregate/sidecar
   pair, and returns only the fixed projection already proven by the source
   adapter.

The model-facing caller has supplementary membership only in
`hlabroker-clients` and a new `aster-doctor-client` socket group. It is not in
`hlabroker-approvers`, `aster`, `aster-lab-broker`, an administrative group, or
any credential-custody group. Aster receives access only to the caller socket
through `aster-doctor-client`; it does not receive broker-client or approval
membership from this candidate.

The proposed AI-PAM enrollment is exact:

- agent `agent-aster-fixed-doctor`, dedicated UID, state `observer`;
- service `aster-fixed-doctor`, proxy mode, no credential;
- Green capability `diagnostic.aster-inference.latest`;
- exactly one grant to that agent; and
- disable path: disable service, revoke the one grant and suspend the agent.

Enrollment refuses an existing identity mismatch, service/capability metadata
conflict, or any additional grant. Changed fixed-capability payloads are denied
before consumption, so they do not create a false consumed audit row or reach
the data gateway.

## Validation

The combined offline suite passes **73/73**:

- 7 producer/scheduler tests;
- 26 fixed adapter, projection, capability, caller, gateway and unit tests;
- 40 broker transport, enrollment, policy-core and unit-regression tests.

It covers kernel-peer denial on both sockets, changed methods and payloads,
wrong caller, policy binding, replay protection, broker/gateway outages,
unsafe files, stale evidence, extra/private result fields, one-grant enrollment,
reversible disablement and absence of approval-group membership.

Pinned implementation hashes:

| File | SHA-256 |
|---|---|
| `ops/credential-broker/broker_admin.py` | `d563afa571cce4018d92f60164f0d9ccf8db8a4144adf3bf0f058321fc1bcf50` |
| `ops/credential-broker/broker_service.py` | `c479cd7f207c2761712f41ef4f2376f17303002c295f44a0486ab77c1c64eb35` |
| `services/aster-agent/fixed_doctor_caller.py` | `aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a` |
| `services/aster-agent/fixed_doctor_gateway.py` | `852e609ef278acee1b4343ea8627d2c01f8f1a2cc42556aeb9acfa184b4bd495` |
| caller unit | `9a4aa0336df27de60483e567cef43360277d0ec4ebbee2fbcb4093e644b055bf` |
| gateway unit | `44ee0df1c163bc453148032f7187c56e38a532377efc5084dadb40d461b629ef` |
| sysusers fragment | `60000eda4e09fab0b1401cc2d6cf7df3e5166c3b10486211736106a136470daf` |

## Remaining gates

No Aster tool definition imports the caller yet. Before installation, freeze a
reviewed bundle and rollback, confirm unused UID/GID allocation, target-Linux
imports and systemd verification, preserve and validate the broker database,
and prove the new caller cannot open the approval socket. Producer deployment,
caller/gateway installation, AI-PAM enrollment, Aster model-route exposure and
the first live read are separable operational changes. This source result
authorizes none of them.

