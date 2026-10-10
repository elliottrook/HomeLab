# Migration and gap analysis

## Before / after

| Area | Brand SVG Studio | Brand Design |
|---|---|---|
| Trigger | `$brand-svg-studio` | `$brand-design`; old name explicit-only compatibility alias |
| Library | Registry, brand brief, master hashes, working/assets/releases/archive | Preserved unchanged |
| Vector edits | Recolour, trace, audit, render, export, package | Preserved and gated behind approved source/raster handoff |
| Initial brand creation | Only lightweight new-brand registration | Full brief, concepts, owner master lock and rejects |
| Precise raster revision | General preservation guidance | Formal edit contract and invariant-region evidence |
| Reference system | No fixed coverage minimum | 18 numbered references or signed one-to-one equivalents |
| Brand documentation | Brand brief and asset metadata | Manual PDF/pages, contact sheet, tokens, reconstruction literature, rights/provenance |
| QA | SVG audit plus real renders | Adds raster/full package validator, literal copy, rights, manifest, ZIP and deployment gates |
| Deployment | Promotion/release after approval | Mandatory deployment decision with approved target, state and rollback |

## Retained files

`scripts/brand_library.py`, `scripts/svg_audit.py`, `references/storage.md`, and `references/svg-workflow.md` are carried forward byte-for-byte in the staged migration. `references/legacy-crosswalk.md` makes preservation auditable.

## Known gaps and decisions

1. The supplied fotosforfun fixture is useful raster/reference proof but contains no production SVGs and lacks several strict rights/approval/hash records. It passes only the deliberately limited `fixture` profile and cannot graduate the raster handoff, vector or deployment paths.
2. Actual font rights and owner approval states inside the old fixture are not converted into new assertions. Unknown rights block promotion/publication.
3. A current runtime invocation can be smoke-tested after install, but a UI/application reload may still be required before automatic trigger discovery updates.
4. Forgejo push needs Jason's immediate explicit confirmation. The checkout also contains an unrelated ahead commit, so any project commit must remain focused and push behavior must not rewrite it.
5. The skill validator uses Python standard library only. The official quick validator could not run in the current default Python because `PyYAML` is absent; frontmatter/interface were checked with Ruby's YAML parser.
6. Deployment may have simultaneous blockers. The record should store all blockers in `blockers[]` while `status` names the first gate encountered in order: missing target, missing approval, unreachable target, then rights/validation.
