# AsterTV v3 M5 pronunciation candidate evidence

Date: 2026-11-05

State: repository-only compatibility candidate

## Outcome

The five pronunciation rules embedded in the accepted cleanup module now have
a strict, data-only v1 representation with stable identifiers, explicit
ordering and locale `en-CA`. A twelve-case synthetic corpus covers positive,
boundary and false-positive behavior. Every retained result is idempotent.

The compatibility verifier accepted only the exact canonical cleanup SHA-256
`0476a393afd237833835b8e5499f64250bfc5e382a1603b94803cb99e7a350b9`
and reported all twelve outputs byte-identical. Four focused tests pass,
including unknown-flag, duplicate-rule and canonical-drift denial.

## Boundary

This is extraction and validation groundwork, not an expanded pronunciation
set. It contains no private book text and does not change the canonical module,
existing generation, reader, renderer, service, catalogue, queue or booking.
Representative real-book cases, any new pronunciation, synthesis/listening
and generation-manifest adoption remain gated. Those steps require a reviewed
content-private corpus and a separately registered, hash-pinned Lab Hours
workload before any speech effect.
