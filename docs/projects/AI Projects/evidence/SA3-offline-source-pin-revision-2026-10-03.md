# SA3 offline evidence source-pin revision

Status: **reviewed local revision; no runtime deployment**  
Date: 2026-10-03

## Trigger

The offline adaptive evidence harness rejected the current Aster source because
its whole-file pin still referenced revision `2c71d6b`. This was the intended
fail-closed response. The current reviewed repository source and deployed LXC
104 source have the same SHA-256 digest:

`343bce00b777134bfb6f28f7e3218bea3a21240ed19f9cb0bad819186ab2deb0`.

## Review method

The harness compiles only four functions and three assignments from Aster:
`select_tools`, `normalized_messages`, `preload_read_only_context`,
`build_payload`, `ASTER_SYSTEM_PROMPT`, `TOOLS`, and `TOOL_HINTS`.

An AST-normalized comparison between the former pinned source and current
source selected 59 lines in each revision and found them exactly equivalent.
The whole-file change therefore does not alter the reviewed offline fixture
slice. The definition has been advanced to the current digest under a new
review reference; no automatic pin refresh is introduced. The separately
namespaced selector probe pins the same whole-file Aster source. Its two
selected elements (`TOOL_HINTS` and `select_tools`) were also AST-equivalent,
so its experiment definition is advanced in this same reviewed revision.

## Validation required

The offline contract, evidence-store, lineage, paired-evaluation,
source-policy, and selector-conformance suites must pass against this new pin
before it can be used as evidence. This revision does not change the Aster
runtime, permissions, model, data collection, or promotion status.
