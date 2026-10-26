# D4 candidate-H descriptor credential boundary — 2026-10-25

**State:** offline candidate prepared; authority **not granted**

The candidate-G semantic contract remains exact and unspent, but its runner
expects ASTER_LLAMA_API_KEY in the process environment. The platform-owned F6
boundary requires an inherited protected descriptor or standard input and
forbids credentials in argv, environment, JSON, journals and logs. Candidate-G
therefore remains non-executable.

Candidate-H makes only the credential-transport correction:

- --key-fd names an inherited descriptor number of at least 3;
- the runner reads at most 4,097 bytes, accepts at most 4,096 printable
  non-whitespace ASCII bytes with one optional trailing newline, then closes
  the descriptor;
- invalid, unavailable, standard-I/O, oversized, empty or non-printable input
  fails closed;
- ASTER_LLAMA_API_KEY is no longer read;
- a dry run does not inspect the descriptor and still reports
  keys_accessed=false; and
- no key value is printed, journaled, placed in a prompt or retained.

The investigation fixtures, response contract, engine, model, runtime, case
order, 12-session and 36-call limits, deadlines and strict 12/12 structural
gate are unchanged.

## Frozen offline identity

- Alias: candidate-H
- Authority: not-granted
- Run digest:
  423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4
- Eleven-file manifest:
  services/aster-agent/evals/sa3-development-attempt-11-source-manifest.json
- Manifest SHA-256:
  5e8b1ca0314fb3deefc9a45f9755f92947b7f14ca53c590e21a14ee50cce0414
- Runner SHA-256:
  af925aeae2197ac27dfb787775f7706c40712147eabdd0825551f62002b6ae5a

Validation passed:

- focused executor tests: 9/9;
- complete evaluation tests: 168/168;
- isolated import-completeness and exact manifest checks;
- descriptor close, size, encoding and standard-I/O rejection; and
- dry-run proof with a deliberately invalid descriptor and a fictional
  environment key, neither accessed.

## Remaining platform boundary

This source change does not itself implement secret delivery. Before any live
card, the platform owner must name and independently review the exact broker
command or service that opens the protected descriptor, its invoking identity,
descriptor number and inheritance behavior, and how it prevents unintended
child inheritance. The live card must pin that bridge and the runner packet,
prove the descriptor is absent from logs/evidence, and retain the existing
one-attempt and recovery rules.

Candidate-H has not been staged or executed. Candidate-G's existing approval
does not transfer to this changed digest. A later approval must name the
candidate-H digest after the platform bridge and the complete F6 transaction
are independently reviewable.
