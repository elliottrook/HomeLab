# M3 J1 bounded training result — 2026-11-03

## Decision

**PASS; exact artifact frozen, still non-authorizing and undeployed.**

Jason approved the exact release candidate frozen at Stream A commit
`907ec8c3` for one bounded offline transaction consisting of two clean CPU
reproductions. Public evaluation, sealed holdout, deployment, routing, tools,
service restart and model/backend change were excluded.

## Execution

The first executor launch failed before importing the recipe because isolated
Python did not add the sibling module directory. It produced no training and no
retained output. The launcher was corrected to add only its own fixed source
directory; its focused tests then passed 4/4 and the exact transaction ran once.

Two fresh isolated workers used the exact v3 corpus, exact seven private
non-overlap receipt bytes, exact private result and exact release manifest.
Network audit events were forbidden. Both workers produced byte-identical
artifact and summary files:

- raw validation exact: 70/80;
- guarded validation exact: 70/80;
- selected margin: `0.375`;
- accepted validation: 50/80;
- accepted exact: 50/50;
- artifact identity: `606bd761…ae7c`.

Only after equality was proven did the transaction retain one artifact,
summary and content-free execution receipt under the human-controlled private
benchmark record. The directory is mode 0700 and all three regular files are
mode 0600. Independent re-read verified file hashes, artifact self-hash,
external release/guard bindings, 16 fixed labels and all frozen metadata.

The exact executor is `c04d7204…a20a`; its tests are `0bfaeb8f…08a`. The exact
executor/recipe/release suite passes 17/17 with the private receipt directory
supplied. Authority remains `not-granted`, automatic routing remains `off`, no
private content is copied into the repository, and no public or holdout gate
has been opened.

## Next gate

The artifact is frozen but not promoted. Before the one-time 24-case public
gate, Stream A must create an exact source-only evaluation packet binding the
retained artifact and execution receipt. A public result may only produce a
promote-or-reject decision; it cannot deploy the classifier, open the holdout,
enable routing or grant tools.
