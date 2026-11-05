# M3 J2 external-custody handoff card — 2026-11-04

## Purpose

Candidate-v4 is accepted for corpus release only. The remaining release gate
is proof that corpus custody is controlled independently of the shared
worktree and main agent. This card is a content-free handoff; it is not a
custody receipt and cannot be self-approved by another agent in the same
workspace.

## Exact object to bind

- preregistration manifest:
  `2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee`;
- corpus:
  `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`;
- normalized text set:
  `a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0`;
- label review:
  `896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028`;
- quality review:
  `f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f`;
- owner acceptance file:
  `9e7eb6f76396088b5650647d0c7970b5659711ff94fd3c0c16fd504619bf393b`.

The content-free facts are 768 training rows, 192 validation rows, 16 labels,
eight overlap references, zero normalized overlap, corpus custodian
`independent-j2-corpus-custodian`, reviewer
`independent-j2-label-reviewer`, content absent from the receipt and authority
`not-granted`.

## Required independent act

An independently controlled human account or signing identity must:

1. obtain the exact candidate and review artifacts through its controlled
   custody path, not by accepting identity strings from this worktree;
2. recompute the five artifact identities and the fixed content-free facts;
3. emit the canonical `aster-nlu-j2-corpus-custody.v1` receipt required by
   `nlu_j2_custody_receipt_v1.py`;
4. bind that exact receipt through a detached signature, separate-account
   audit record or equivalent independently verifiable control; and
5. return only the content-free receipt and proof. Corpus text, review rows,
   private source material and evaluation content must not enter Git or chat.

## Acceptance and exclusions

Stream A may validate the returned receipt against the frozen validator and
all exact local artifact bytes. It must reject a shared-worktree-generated
receipt, unauthenticated role string, digest mismatch, changed fact, missing
independent proof or uncertain custody.

Even a valid corpus-custody result does not authorize training. A third,
distinct evaluation custodian must still create and seal the preregistered
32-case evaluation set before training admission can be considered. Model
calls, training, sealed-evaluation access, deployment, authority and automatic
routing remain off.
