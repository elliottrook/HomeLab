# M3 K2 MacBook sealed-shortlist boundary — 2026-11-06

## Outcome

The source-only MacBook stage that will derive K2's four-label shortlists from
the independently sealed evaluation is frozen and passes its focused tests.
No sealed file was opened and no model request was made.

## Fixed boundary

- source: `scripts/aster-adaptive/nlu_k2_apple_embedding_sealed_shortlister_v1.swift`
- source SHA-256: `cf06a32a53ac1d76a9da47f7b7262ad9c7a10ec494685215d7e612369a877077`
- focused test SHA-256: `b4c332f1b3e1fae877ce1798dcb375e0456cc270e496aa2a7a6f59f868169576`
- accepted corpus SHA-256: `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`
- independently sealed evaluation SHA-256: `78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae`
- shortlister: Apple NaturalLanguage 300-dimensional English embedding,
  768 accepted training rows, normalized per-label centroids and deterministic
  top-four ordering
- output: one create-only, no-follow, mode-0600 private file containing case
  identifiers and four-label shortlists; standard output contains only schema,
  dimension, row count and `authority=not-granted`

The stage validates the exact corpus and evaluation bytes, exact sealed
metadata, 16 labels, 48 training rows per label and two evaluation cases per
label. It does not contain a network client, service credential, absolute
private path, route effect or model transport.

## Verification

- focused Python source tests: 4/4 passed
- Swift typecheck: passed with a private temporary module cache
- sealed evaluation access: false
- model requests: zero
- B60 use: none
- deployment or routing authority: not granted

## Remaining gate

This boundary cannot be executed until the currently booked K2 development
transaction passes with production restored and the sealed-evaluation effect
has its own admissible Lab Hours reservation, registered hash-pinned workload,
lease and shared operation lock. A later private runner must keep sealed text
on the MacBook and return only bounded private result material for local
scoring; this source freeze does not authorize that effect.
