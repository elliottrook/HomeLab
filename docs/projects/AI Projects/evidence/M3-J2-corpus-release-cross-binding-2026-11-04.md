# M3 J2 corpus-release cross-binding — 2026-11-04

## Decision

**SOURCE READY; NO CORPUS RELEASE OR TRAINING AUTHORIZATION EXISTS.**

The corpus-release validator closes the gap between the J2 corpus, its
960-row semantic review and the content-free custody receipt. It recomputes
and requires the exact corpus-byte digest, normalized-text-set digest and
review-byte digest; requires the frozen corpus custodian and label-reviewer
identities; requires 960 accepted rows and zero corrections; and keeps
training authorization false, authority not granted and automatic routing off.

The custody receipt now requires exactly eight overlap references rather than
silently accepting extras. Combined J2 source tests pass 35/35. Synthetic
fixtures prove the fail-closed binding behavior; they do not claim that a real
corpus, review, signed custody record or sealed evaluation exists.

## Remaining gate

The source boundary still cannot authenticate independent custody from strings
inside a shared worktree. A real release candidate needs the six exact raw
calibration corpora from human-controlled custody, successful pinned
zero-overlap validation, complete independent semantic review and externally
controlled signer evidence. Evaluation data must remain outside trainer and
main-agent access. No model call, training, booking, service effect, route or
deployment was authorized or performed here.
