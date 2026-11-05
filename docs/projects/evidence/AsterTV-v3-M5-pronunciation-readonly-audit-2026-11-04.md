# AsterTV v3 M5 pronunciation read-only audit

Date: 2026-11-04

State: audit complete; no speech or catalogue effects

## Result

The accepted narration cleanup is reproducibly pinned, but it does not yet
have the versioned pronunciation lexicon and representative regression corpus
required by M5. The current corrections are executable rules inside a single
Python module. Expanding those rules in place would change every future
narration generation and make individual pronunciation changes difficult to
review, test or roll back.

No private book text, credential, model, narration job or reader state was
read or changed during this audit.

## Retained contract

- Canonical module:
  `/opt/epub-narration/vendor/digest_text.py`
- SHA-256:
  `0476a393afd237833835b8e5499f64250bfc5e382a1603b94803cb99e7a350b9`
- The worker passes this exact path to the renderer.
- The renderer imports only `speech_text` and `narration_units` and the
  publication path pins the cleanup hash in ready-generation manifests.
- Current pronunciation/normalization rules cover Markdown links and emphasis,
  bare URLs, United States and British Columbia dotted abbreviations, Saint
  Petersburg, emergency 911 context, Roman numerals, currency and grouped
  integers, parentheses/punctuation cleanup, and Lutron Caseta.
- Long-form narration is divided into bounded sentence/clause units with
  explicit pauses; that behavior is part of the same module and must remain
  independently stable when pronunciation data is extracted.

## Regression gap

The retained renderer test proves the cleanup hash and one combined synthetic
sentence containing British Columbia, a grouped dollar amount and a URL. It
does not independently exercise every accepted rule, conflicting matches,
case handling, punctuation boundaries, possessives, false positives, chapter
unit boundaries or idempotence. There is no separately identified lexicon
version in generation metadata.

## Safe next slice

1. Define a data-only, schema-versioned pronunciation lexicon with stable rule
   identifiers, ordering and an explicit locale.
2. Preserve the current module hash and ready generations as the sentence-timed
   fallback; do not rewrite existing manifests.
3. Build a synthetic, non-copyright corpus containing one positive, boundary
   and false-positive case per retained rule plus idempotence and ordering
   checks.
4. Add a compatibility adapter whose output is byte-for-byte identical to the
   accepted cleanup for the retained corpus before adding any new entry.
5. Give each proposed expansion its own expected spoken form and listening
   rationale. Do not infer real-book names or pronunciations from private text.
6. Treat representative synthesis/listening as an exclusive local-AI workload:
   register and hash-pin it, check and reserve the complete Lab Hours window,
   acquire the whole-host lease and shared lock, and retain content-free
   evidence.
7. Promote only through new generation manifests after interruption, rollback,
   reader compatibility and listening acceptance pass. Existing generations
   remain valid and unchanged.

This audit authorizes no Aster Speech installation, model execution, backlog
processing or reader/catalogue promotion.
