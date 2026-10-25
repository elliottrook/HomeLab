# M3 NLU llama response-envelope compatibility — 2026-10-25

> Result: **OFFLINE CORRECTION PASS — NO MODEL CALL**

## Finding

The calibration adapter deliberately accepts only an exact, tool-free
classification envelope. The transport runner previously passed the complete
HTTP response directly to it. Retained B60 harness fixtures show that the
accepted llama.cpp API includes ordinary OpenAI-compatible response metadata
such as `usage` and llama timing fields. Those valid metadata fields would
have caused every otherwise valid calibration classification to be rejected.

## Correction

At source commit `4a7adab5`, the runner now validates a fixed allowlist of
known llama/OpenAI envelope and choice metadata, extracts only `message` and
`finish_reason`, and passes that normalized shape to the unchanged strict NLU
adapter. Unknown envelope or choice fields still fail closed. Message fields,
classification schema, no-tool semantics, engine/policy bindings and retained
content-free output are unchanged. `usage`, `timings`, model identifiers and
other response metadata are discarded and never enter calibration evidence.

## Evidence

- runner SHA-256:
  `b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11`;
- staging manifest SHA-256:
  `357b4e3d5514fe32b1509ac27f9eac3940edb0635db3a5008b4f29fc4f124a00`;
- staging validator SHA-256:
  `eab93406dbde22849f5a884a588744656a6ac175b641032517672a3fb77d46f4`;
- focused runner/staging tests: **19/19 passed**; and
- dependency-free NLU suite: **113/113 passed**.

The real ten-input Mac source packet was revalidated against the updated
manifest: 10/10 inputs and 93,612 aggregate bytes matched. No LXC file was
staged, no credential was read into evidence and no model request, score,
threshold, route or production change occurred.

