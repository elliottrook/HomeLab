# Brand Creation Standard

## Purpose

This is the reusable project standard invoked by `$brand-design` for new identities, broad redesigns, narrowly scoped brand edits and production SVG delivery. It carries each brand engagement from an exact brief and approved source through documented assets, vector production, release QA and an authorized deployment decision.

It supplements the repository's general security, authorization and evidence rules. It does not grant permission to publish publicly, push a protected remote, use unlicensed material or overwrite an approved master.

## Systems of record

| Material | Canonical home |
|---|---|
| Workflow and routing instructions | Installed `$brand-design` skill |
| Reusable standard and templates | This repository under `docs/standards/brand-design/` and `docs/templates/brand-design/` |
| Brand registry and approved release metadata | Brand Asset Library |
| Original supplied material | Brand's immutable `incoming/` area |
| Active engagement state and drafts | Brand's `working/<date>-<job>/` area |
| Approved production assets | Brand's `assets/` area |
| Reproducible source/build material | Brand's `sources/` area |
| Immutable delivery packages | Brand's `releases/` area |
| Superseded approved assets | Brand's `archive/` area |

## Standard brand directory

```text
Brand Asset Library/brands/<brand-id>/
  brand.json
  BRAND-BRIEF.md
  approved-master-hashes.json
  incoming/
  working/<YYYY-MM-DD>-<job>/
  assets/
  sources/
  releases/
  archive/
```

Do not place brand-specific generated images or large releases in the HomeLab Git repository unless a later repository policy explicitly designates a small, rights-cleared fixture.

## Required invocation sequence

### M0 — Discovery, target and risk

Resolve the exact brand, current approved master, applicable product/brand guide, canonical asset directory, requested deployment target, repository rules, available generators/renderers, font and image rights, privacy constraints, accessibility needs and authorization boundaries. Record exclusions, rollback and stop conditions.

### M1 — Brief and rights gate

Record exact literal spelling and copy, purpose, audience, uses and sizes, tone, preferences/dislikes, accessibility, relevant personal or cultural cues without stereotype, consent/provenance, font and image rights, destination and the latest approved source for revisions. Unknown rights permit clearly marked local drafts only; they block promotion and publication.

### M2 — Concepts or edit contract

For new or broad work, create at least three materially distinct directions unless the owner chooses another count. Record comparisons and rejected concepts.

For a narrow revision, create an edit contract with `base_image`, `requested_region`, `requested_delta`, `invariant_regions`, `approved_palette` and `reference_source`. Prove isolation with masks, deterministic compositing or an invariant-region comparison. Generative editing alone is not proof that other pixels stayed fixed.

### M3 — Master approval and source lock

The owner approves one exact file/version. Record its SHA-256 and preserve it unchanged. No downstream expansion or approved-master replacement occurs from an ambiguous or unapproved candidate.

### M4 — Asset plan and reference production

Instantiate `ASSET_ORDER_SHEET.csv`. Produce all 18 numbered references or an explicitly approved one-to-one equivalence map. Record actual dimensions, effective native detail, transparency, consumer output, approval, rights and QA. Interpolation does not create native detail.

Create isolated closeups and reconstruction literature covering literal text, glyph quirks, layer IDs, geometry and curve intent, drawing order, overlaps, brush tails, counters, gradients, spacing, clear space, minimum size, transparent boundaries and micro-size simplification.

### M5 — Identity manual and applications

Create a multi-page PDF manual and PNG preview of every page. Cover story/values; primary, horizontal, stacked, compact and icon alternatives; dark/light and monochrome; watermark; palette and gradients; typography/licenses; clear space and minimum size; misuse; relevant web, app, social, photo and print applications; delivery formats and known limitations. Produce an asset contact sheet and label mockups as contextual examples.

### M6 — Raster handoff gate

Validate the approved-master hash, literal spelling, 18/equivalence matrix, paths, decoded image integrity, dimensions, effective resolution, rights, approvals, manual/pages, contact sheet, reference-to-consumer mapping, manifest and offline ZIP. Preserve the original input. Use the strict `raster` validator profile; a `fixture` pass is not this gate.

### M7 — SVG reconstruction and vector QA

Reconstruct editable paths and meaningful layers rather than embedding raster artwork. Preserve exact wording, bespoke signature outlines, optical spacing, shape topology, counters, gradients and overlap order. Produce appropriate dark/light, monochrome and simplified micro variants.

Parse and sanitize every SVG. Reject scripts, event handlers and unapproved external references. Classify any authorized embedded raster. Verify viewBox, fonts/outlines and licenses, local references, geometry, contrast and practical small sizes. Render on light/dark backgrounds and compare in more than one available renderer where practical.

### M8 — Release and package

Generate required SVG, PNG, WebP, favicon/icon, PDF/print and other target exports from the approved source. Record reproducible recipes, manifests and checksums. Reopen the final ZIP, verify its contents and hashes, and render from the packaged copies. Complete machine checks and human visual/intent review separately.

### M9 — Deployment decision and evidence

Every invocation reaches a deployment decision. Install or publish only to the approved target with the authorization required for that target. A private canonical asset-store release counts only after promotion and retrieval verification. Public publication, protected remote writes and Forgejo pushes retain their separate immediate approval requirements.

Record every blocker, with the primary status selected in this order: missing target, missing approval, unreachable target, rights/validation. Never call a preview, commit, local ZIP or staged file deployed. Record destination, release/revision, verification, executor, timestamp and rollback.

## Required engagement files

Each brand engagement instantiates the templates and maintains:

- project state and milestone ledger;
- brief, risk and rights record;
- concepts/comparison and approval record;
- immutable approved master and checksum;
- edit contract when applicable;
- asset order sheets in CSV and Markdown;
- tokens, reconstruction brief, usage and limitations;
- manual PDF/page previews, contact sheet and relevant mockups;
- editable SVG masters and deterministic build/export instructions;
- design, vector and deployment manifests;
- QA report, checksums and final versioned ZIP;
- deployment record and rollback.

## Completion criteria for an engagement

A brand engagement is complete only when every applicable milestone is evidenced, the owner-approved master and deliverables validate, release retrieval succeeds at the approved destination, rollback is recorded, residual limitations are accepted and no action is reported as performed when it was blocked.
