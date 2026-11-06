# M3 J2 single-owner isolated-agent custody decision — 2026-11-06

## Decision

Jason is the only available human operator. He directed Stream A to use
separate Codex instances on his laptop for the remaining J2 corpus-custody and
sealed-evaluation roles. This replaces the unavailable multi-human custody
assumption with a narrower, accurately described assurance model:

`single-owner / independently sandboxed AI custody`

This is procedural independence, not independent organizational control. It is
acceptable for this private HomeLab release candidate only when all controls
below pass. It does not establish a reusable claim that two ordinary agents in
one chat, agent tree or shared worktree are independent.

## Required isolation

The corpus custodian and evaluation custodian must run in two fresh Codex
sessions with no inherited Stream A conversation. Each session receives a
different role-specific workspace. It must not receive the other role's
private key or writable workspace.

Each custodian generates a distinct RSA-2048 key inside its private workspace.
Only the canonical public-key JSON, detached content-free proof envelopes and
content-free receipts return to Stream A. Private keys never enter Git, chat,
the Stream A worktree or the other custodian's workspace.

The evaluation custodian authors and retains the exact 32 cases in its private
workspace. Neither the cases nor their request text may return to Stream A,
the trainer, Git or chat. The evaluation agent receives the accepted corpus
only to calculate the preregistered exact normalized-set intersection. It may
not inspect an existing sealed holdout, historical private evaluation result,
J1 public failure set or another candidate's answer keys.

For meaningful same-laptop separation, each private workspace should be a
separately encrypted volume or a separately permissioned macOS account. Merely
opening two Codex windows on the same directory does not satisfy this decision.
The private volume is unmounted before its content-free outputs are returned to
Stream A. The owner retains its recovery material offline.

## Source enforcement

`nlu_j2_evaluation_v1.py` validates the new sealed-evaluation shape, exact
32-case/two-per-label balance, canonical metadata, accepted corpus identity,
normalized uniqueness and zero exact normalized intersection. It returns no
request content.

`nlu_j2_custody_kit_v1.py` is create-only for keys and outputs. It validates the
accepted corpus/review identities or sealed evaluation, generates canonical
content-free receipts, signs exact proof statements with RSA-2048
PKCS#1-v1.5/SHA-256 and immediately verifies each signature with the existing
frozen verifier. It never writes or copies the evaluation content.

The corpus path was smoke-tested against the real accepted candidate-v4 files
and all eight exact reference artifacts. An initial deliberately retained
failure showed that the similarly named `j1-v3-private-review` calibration
files are content-free review receipts rather than case corpora; the tool
failed before emitting any receipt. Using the six exact `nlu-calibration-v*`
`cases.json` files plus the pinned development and J1-v3 fixtures then returned
`complete`, 960 accepted rows, zero overlap and a self-verified detached proof.
That temporary Stream A key and proof are test material only and are not an
independent custody result.

The role prompts are:

- [corpus custodian prompt](M3-J2-CORPUS-CUSTODIAN-PROMPT-2026-11-06.md)
- [sealed evaluation custodian prompt](M3-J2-EVALUATION-CUSTODIAN-PROMPT-2026-11-06.md)

The kit builder copies only non-secret source and produces a canonical
SHA-256 inventory. Private inputs must be placed into the resulting encrypted
workspaces by Jason or by the isolated custodian session; they are never added
to the kit manifest.

The owner-side `stage_nlu_j2_isolated_custody_inputs_v1.py` command removes
manual path selection from that step. It pins every accepted source digest,
copies eleven exact corpus-role inputs or the one evaluation comparison input
with create-only mode-0600 writes, rereads every copy and rolls back its own
partial copies on failure. It returns paths and digests only. It does not copy
either private key or any future sealed evaluation.

## Acceptance and exclusions

Stream A may pin the returned public-key fingerprints only after checking that
the keys differ, the two role IDs are exact, the kit manifests match, all
signatures verify and the sealed-evaluation receipts bind zero intersection.
The label-review identity remains distinct from both custodians.

Admission can advance only to
`eligible-for-owner-training-effect-review`. This decision does not authorize
training, a Lab Hours booking, sealed-evaluation disclosure, routing, tools,
authority, deployment, a model/backend change or automatic promotion.

If either workspace was shared, either private key escaped, evaluation content
was returned, the same key was reused, an input identity changed or the
custodian cannot account for its isolation, the corresponding receipt is
rejected and no training follows.
