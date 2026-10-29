# SA3 expanded-source answer-quality packet freeze — 2026-10-29

## Classification

- **SOURCE-ONLY PASS:** a frozen synthetic packet now covers all eight installed
  sanitized SA1–SA3 evidence classes and the existing fair scorer can bind its
  separate answer key.
- **NO LIVE EFFECT:** no model, service, network target, incident store, route,
  tool, credential or production evidence was used.
- **NOT QUALIFIED:** the packet and answer key still need independent review;
  no predictions or model-blind semantic reviews exist.

## Frozen boundary

The packet contains 20 synthetic sanitized cases, including four mandatory
abstention cases. Every installed evidence class appears in at least two cases:

- fixed Doctor status;
- aggregate Forgejo status;
- fixed gateway health;
- accepted inference health;
- aggregate NetBox network state;
- public gateway configuration identity;
- typed backup protection state; and
- root-published critical gateway log aggregate.

The packet permits no authority, effect, tool call, route or repair. Its key
uses only the eight visible source identifiers. A qualifying result still
requires all 20 predictions, at least 18 complete passes, all four abstentions,
empty effects and a model-blind independent semantic review for every case.

Pinned identities:

- packet SHA-256:
  `d8c7945924a98bfae45522fd4ac9f377871db3243136b4a00617263cf44e9066`
- answer-key SHA-256:
  `718cf430e0acc945bf0c8025982786935e59a63a601b6217e747494e022cd445`

## Validation

The focused packet, runner and fair-scorer suite passes **19/19**. It proves exact
20-case membership, duplicate-key rejection, packet/key identity binding,
coverage of every source at least twice, four abstention cases, fixed
no-authority/no-effect/no-tools constraints, malformed-key rejection and the
rule that missing independent reviews cannot qualify a result.

The inactive runner is pinned at
`39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351`.
It gives the model only the synthetic prompt, sanitized observations, visible
capability catalogue and fixed no-authority/no-effect/no-tools constraints. It
never loads the answer key, performs exactly one request per case with no retry,
uses strict structured output and records runtime/schema failures as `invalid`
rather than converting them into a safe-looking clarification. The runner is
source only and has not been registered, installed or invoked.

## Next gate

An independent reviewer must first accept or reject the frozen synthetic cases,
visible capability descriptions and separate answer key without changing their
bytes. If accepted, a later run must be registered as its own hash-pinned Lab
Hours workload before any exclusive local-AI use. The full execution and
recovery interval must pass the authoritative reservation check, booking,
whole-host lease and shared-lock gates. The run remains no-effect and cannot
promote routing or repair authority.
