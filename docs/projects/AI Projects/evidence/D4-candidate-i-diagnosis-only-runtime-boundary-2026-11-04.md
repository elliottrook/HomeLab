# D4 candidate-i diagnosis-only runtime boundary — 2026-11-04

Candidate-i's offline runtime source is complete and still unrun. The model
response schema contains only one bounded `diagnosis` string. Deterministic
code owns outcome, evidence checks, effects, authority and the entire explicit
`Verification:` clause. Secret-dependent and no-usable-evidence cases make no
transport call.

The key-free batch binds untouched packet
`0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0`,
requires exactly 20 cases and exactly 14 model requests, and fixes retries at
zero. The batch and runner do not import answer keys or review code. Known
llama metadata is accepted only through fixed allowlists; unknown metadata,
expanded fields, unsafe prose, malformed JSON and transport failure all fall
back to the deterministic diagnosis while preserving the error class.

The candidate manifest now binds six exact runtime/source files. The focused
candidate-i suite passes 22/22. No frozen quality case has been sent to the
candidate or a model, and no key or review judgment was exposed. There is no
booking, effect, route, repair grant or promotion. The next milestone is a
platform-side hash-pinned registration and inactive transaction package.
