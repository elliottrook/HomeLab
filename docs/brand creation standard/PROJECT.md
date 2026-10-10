# Brand Creation Standard and unified Brand Design skill

**Status:** Active locally; Stream M; remote synchronization and public publication unapproved  
**Owner:** Jason  
**Started:** 2026-10-10  
**Canonical repository:** Forgejo `https://git.elliottrook.com/jason/homelab.git`  
**Detailed project path exception:** `docs/brand creation standard/` is retained because the work order explicitly requires it; the portfolio in `docs/projects/README.md` remains the repository index.

## Purpose and desired outcome

Replace the installed Brand SVG Studio identity with one discoverable Brand Design skill that takes a new or revised identity from brief and approved master through documented references, brand manual, editable SVGs, exports, packaging and an authorized deployment decision. Preserve every proven SVG/library feature. Never represent staging or a ZIP as deployment.

## Current state and evidence

- Preflight checkout: `/Users/jasonelliott/AI_Projects/homelab`, `main`, HEAD `ab6daab21ffb9fdba35853857f9e7d56c76f134a`, one unrelated local commit ahead of `origin/main` at discovery.
- Forgejo `origin` is authoritative. GitHub is an automatic protection mirror and is not a write workaround.
- Governing files read: `AGENTS.md`, `docs/Project-Creation-Standard.md`, `docs/Standards.md`, `docs/projects/README.md`.
- Existing runtime: `/Users/jasonelliott/.codex/skills/brand-svg-studio`; canonical asset store: `/Users/jasonelliott/Documents/Brand Asset Library`.
- Existing behavior inventoried in `MIGRATION_AND_GAPS.md`. Original scripts and references are retained in the new skill.
- Supplied fotosforfun fixture has 18 numbered PNGs, five manual-page previews, manual PDF and contact sheet. It is raster proof material, not a completed vector set.

## Scope and exclusions

In scope: installed skill migration/alias, provider-neutral project gates, package validator/tests, fixture validation, project and evidence records, canonical private asset-store installation when the full release is approved, SVG controls, release/deployment records and rollback.

Excluded without a new approval: public publishing, direct GitHub push, force push, public Forgejo ingress, credential disclosure, a fabricated website, claiming that fixture rasters are editable vectors, and overwriting approved brand masters.

## Authority model

| Fact | Authority |
|---|---|
| Repository code/docs | Forgejo `origin` after an authorized push |
| Local pending changes | The named local checkout until synchronized |
| Brand-specific approved assets | Brand Asset Library registry and each brand's current release/hashes |
| Project policy | `AGENTS.md` and `docs/Project-Creation-Standard.md` |
| Deployment state | Per-run `DEPLOYMENT_RECORD.json` plus retrievable target evidence |
| Chat/project handoff files | Inputs/proposals only, never deployed-state authority |

## Architecture and data flow

`brief -> rights/risk -> concepts -> owner master/hash -> coverage/references -> manual -> raster validation -> SVG reconstruction -> vector/render/security QA -> exports -> package -> authorization -> target install/publish -> retrieval verification -> rollback record`

Brand-specific work is kept in the library under `working/`, then promoted to `assets/` and an immutable `releases/` ZIP only after approval. Skill installation is separate from brand-output deployment.

## Privacy and security design

Use least privilege, private targets by default and local validation. No secret-bearing configuration belongs in Git or evidence logs. Supplied photos, personal imagery, fonts and cultural motifs require provenance/consent/license review. SVGs reject scripts and unexpected external references. Protected remote writes and public publication require current explicit approval.

## Pre-start risk assessment

| Risk | Impact | Control / rollback | Stop condition |
|---|---|---|---|
| Loss of SVG Studio behavior | High | Preserve scripts/references; crosswalk and legacy tests; keep recoverable old directory | regression failure |
| Wrong master or unintended edit drift | High | immutable source SHA; edit contract; invariant diff and owner review | uncertain source or changed invariant region |
| Misleading resolution/vector claims | High | actual dimensions/effective-detail field; SVG audit; embedded raster classification | upscaling or wrapped PNG called native/vector |
| Rights/privacy/licensing failure | High | provenance, consent, font/license status; local draft only | public/promotion rights unresolved |
| Unsafe SVG | High | XML parse, external/script detection, renders | executable/external content not explicitly approved |
| Unapproved remote/public mutation | High | Stream M, immediate approval, Forgejo only | missing current authorization |
| Existing unrelated local commit | Medium | focused paths/commit; no reset/rewrite | overlap or ambiguous history |
| Cloud agent cannot reach private Forgejo | High | pull-based Tailscale local runner proposal | never open public ingress as workaround |

No production service interruption is expected. Recovery is directory-level rollback of the installed skill and immutable library releases. Synthetic brand tests avoid customer data.

## Persistence and resume

Read `STATUS.json` and `EVIDENCE.md`; rerun the recorded test commands. Do not infer completion from checked-in plans. The next safe action is the first incomplete milestone whose prerequisites and approval are satisfied.

## Milestones

- [x] **M0 discovery:** repository, policies, remote, skill, library and fixture found; risks recorded.
- [x] **M1 merge design:** old-to-new crosswalk, compatibility alias and contract defined.
- [x] **M2-M4 workflow:** intake/edit gates, 18-reference matrix, manual/mockup and raster validation requirements implemented in skill instructions.
- [x] **M5 vector integration:** original SVG workflow and audit script retained; safety and fidelity gates incorporated.
- [x] **M6 package pipeline:** offline validator and synthetic tests implemented; supplied material passes only the deliberately limited fixture profile.
- [ ] **M7 deployment:** install new skill and alias; invoke after reload; brand output deployment remains blocked until a complete vector release and approved target exist.
- [ ] **M8 end-to-end:** synthetic validator tests pass; fotosforfun proves the basic fixture shape but fails the strict raster/full gates, so rights/approval/hash records, vector production and visual owner signoff remain open.
- [ ] **M9 graduation:** requires runtime trigger proof, full brand release/deployment or explicit scope acceptance, focused commit, authorized Forgejo push, and mirror verification.

## Validation and evaluation

Positive tests cover a synthetic 18-asset raster package and the supplied fotosforfun raster fixture. Negative tests cover missing PNG, corrupt PNG, duplicate/missing IDs, literal-name mismatch, and a full package missing SVG/deployment records. Full release validation additionally checks manifest paths/hashes/rights/approval, deployment state/rollback, SVG presence and ZIP integrity. Visual fidelity and owner intent always require human inspection.

## Observability and maintenance

HomeLab Doctor, monitoring, NetBox, Homepage, DNS, certificates, firewall and diagrams are not applicable: this local skill/library change creates no running service, address or network path. The specialist proposal recommends audit/status hooks if a future runner is implemented. Periodic automation is not introduced.

## Backup, restore and rollback

Before installation, preserve the current installed `brand-svg-studio` directory. Install `brand-design` as a new directory and replace the old directory only with an explicit-only compatibility shim. Roll back by removing the new directories and restoring the preserved copy. Brand releases remain immutable; promotion archives the previous approved assets before replacement.

## Documentation and systems-of-record checklist

- HomeLab Doctor / monitoring / NetBox / wiki / Aster mirror / operational runbooks / diagrams / Homepage / DNS/firewall: not applicable until a runner or network service is approved and deployed.
- Backup and recovery: directory/release rollback specified above.
- Repository documentation: this project, evidence, migration/gap record, portfolio and changelog.
- Authentication/authorization and AI administration: specialist report covers a future least-privilege Forgejo path; no identity or credential created here.
- Security inventory: no credentials stored; hashes and non-secret paths only.

## Graduation criteria

The installed `$brand-design` trigger must load after activation, legacy SVG behavior must regress cleanly, a full package must validate and be retrieved from an authorized destination, rollback must be recorded, all limitations accepted, and Forgejo/mirror SHAs verified after explicit push approval.

## Evidence log

See `EVIDENCE.md`. Checkboxes are evidence claims and remain open where the supplied fixture cannot prove vector production or deployment.

## Close-out

Not eligible. Current local implementation is a staged/installed skill engineering result with truthful open M7-M9 gates.
