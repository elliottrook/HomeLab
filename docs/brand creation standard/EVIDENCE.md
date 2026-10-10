# Evidence index

## 2026-10-10 preflight

- Local checkout: `/Users/jasonelliott/AI_Projects/homelab`; branch `main`; HEAD `ab6daab21ffb9fdba35853857f9e7d56c76f134a`; `origin/main` at `586457f`; tree clean, local branch one commit ahead.
- Remote: Forgejo `https://git.elliottrook.com/jason/homelab.git` for fetch/push. No credentials printed.
- Policy source revision for inspected standards: `9153640cf84425f29e375079aaf211730621225f` (latest commit touching the queried policy paths).
- Skill source: `/Users/jasonelliott/.codex/skills/brand-svg-studio`.
- Asset store: `/Users/jasonelliott/Documents/Brand Asset Library`, resolved by original `references/storage.md` and library `AGENTS.md`.

## Build and test

- Staged skill retains both original scripts and references and adds `brand-workflow.md`, the handoff contract, 18-row baseline CSV, compatibility crosswalk and offline validator.
- Synthetic test command: `python3 -m unittest discover -s work/staging/brand-design/tests -v`.
- Result: 7/7 passed after independent forward-test hardening. Negative cases: missing PNG, corrupt/CRC-invalid PNG, duplicate ID, wrong literal text, insufficient raster metadata/records and missing full-release records/SVG/deployment.
- Fixture command: `python3 work/staging/brand-design/scripts/validate_brand_package.py work/fixture/fotosforfun_codex_handoff_v1 --profile fixture --expected-text fotosforfun`.
- Result: fixture-profile pass, 18 references; manual PDF, five page PNGs and contact sheet detected. This is intentionally not a raster-gate or full-release pass.
- Official `quick_validate.py` attempt: blocked by missing `yaml` Python module. No dependency was silently installed.
- Installed skill: `/Users/jasonelliott/.codex/skills/brand-design`; `SKILL.md` SHA-256 `09d5ef2f888bc27dccceedcb907ea8eae11561680f6371fc4d8af18bc171feea`.
- Rollback copy: `/Users/jasonelliott/.codex/skills/.brand-svg-studio-backup-20261010`; legacy `brand_library.py` and `svg_audit.py` are byte-identical in Brand Design.
- Legacy alias: `/Users/jasonelliott/.codex/skills/brand-svg-studio`, explicit-only, routes to `$brand-design`.
- Post-install tests: 7/7 passed. Installed registry resolved `fotosforfun`; master-hash verification returned clean with zero approved files because no asset was promoted.
- Independent forward-test agent: `/root/brand_design_smoke`. It selected the correct raster-to-vector route, refused to claim SVG/deployment, and found validator undercoverage. The validator was then split into limited `fixture`, strict `raster`, and `full` profiles; PNG chunk CRC/IEND checking and strict matrix/record requirements were added.
- fotosforfun immutable input ZIP SHA-256: `f4782a299df875ec7efbeceb8a80662311b7a9f9b7b8adcc7a75b6017611e9cf`; `unzip -t` reported no errors.
- Current brand-output deployment record: `blocked_rights_or_validation`. The canonical target is known, but no approved editable SVG release or complete rights/license record exists; nothing was promoted to `assets/` and `current_release` remains null.

## Specialist

- Separate agent `/root/forgejo_tailscale` produced `FORGEJO_TAILSCALE_CLOUD_AGENT_ACCESS_PROPOSAL.md`.
- Recommendation: pull-based Tailscale-joined local runner applying immutable reviewed bundles; gated mirror/staging next; narrow broker only if interactivity is essential. No production/network/credential changes were made.

## Pending proof

- Installed skill path/hash and post-install invocation.
- Full fotosforfun editable SVG set and full-profile validation.
- Authorized target installation/retrieval and rollback exercise.
- Focused local commit SHA.
- Explicitly authorized Forgejo push and actual Forgejo/GitHub mirror SHAs.
