# AsterTV brand-asset authority reconciliation — 2026-11-06

## Scope

Replace remembered workstation-path guidance with the canonical private
Forgejo Git LFS repository. This was documentation, catalogue and skill work
only; no AsterTV appliance, Remote deployment, network rule or brand repository
was changed.

## Authority verified

- Repository: `git@192.168.20.30:jason/brand-assets.git`
- Branch: `main`
- Inspected revision: `2bdb72732f67e117da6be34da914f16f043e2dce`
- Brand: `aster-home` (`Aster Home`)
- HomeLab migration/recovery receipt: active and verified on 2026-11-06
- Recovery evidence: 2,591 files; 4,363,230,287 bytes; 115 approved hashes;
  post-import LXC backup, independent TrueNAS copy and isolated restore recorded
  by `docs/projects/Brand-Asset-Library-Forgejo.md`

The repository was cloned through the existing authorized SSH identity with
smudging disabled, then the two relevant Aster project directories were
materialized with the checksum-pinned Git LFS 3.8.1 Darwin arm64 binary. The
downloaded archive matched SHA-256
`0ba10e897e0496412cd86eacaed4ed554c97ddc29bc5c709d28faa5eaaa2222c`.
The inspected PNG, SVG and QA comparison files decoded as real assets rather
than LFS pointers.

## Approval boundaries preserved

| Asset | Exact source | SHA-256 | Consumer state |
|---|---|---|---|
| AsterTV primary logo R5 | `brands/aster-home/working/2026-11-04-approved-r5/SVG/32-aster-tv-logo.svg` | `747aab438334afc9b1e2a0dafa8608bd8b8d4aa5ed29af5697f22972b714d2e8` | Owner-approved project master; no global Aster Home release is recorded |
| AsterTV Remote SVG reconstruction | `brands/aster-home/working/2026-11-05-aster-tv-remote-svg/SVG/AsterTV-Remote.svg` | `7effb1ffe3ba828de63059235c976f26e0d7fb869e0856d0fb52cea86a775ada` | Faithful reconstruction for owner review; promotion/install remains blocked on owner acceptance |

The Remote asset is a launcher/app-icon candidate. It does not change the
accepted in-app rule that limestone-backed compass art is excluded from top
rails, pills and ordinary controls.

## Validation

- Aster Home resolver returned the expected `aster-home` directory and no
  global `current_release`.
- Aster Home approved-master verification reported zero failures (and zero
  globally recorded masters); project approval records therefore remain
  essential for the two files above.
- AsterTV generated outputs: 29/29 reproducible.
- AsterTV design tests: 12/12 passed.
- Codex skill build/install tests: 3/3 passed.
- The installed `astertv-design-engineer` entry point matches the source skill
  hash `bfcada357e15afded9414a19bad164ab34e7cc4d9fce31ed7e21e7cb61d1b0bd`.

## Residual gate

Do not deploy or promote the Remote SVG until the owner accepts the rendered
reconstruction. Do not claim that later asset-repository revisions are backed
up until the external recovery receipt records them.

