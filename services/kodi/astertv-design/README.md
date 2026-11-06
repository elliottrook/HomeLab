# AsterTV design authority

This directory is the machine-readable consumer authority for the AsterTV
television surface. It does not replace the Branding Agent's private Forgejo
asset repository, and it does not deploy a skin. It records how
approved assets, tokens, components, pages and remote-first focus behavior are
consumed.

## Approved asset source

The canonical pull source is:

```text
git@192.168.20.30:jason/brand-assets.git
  branch: main
  brands/<brand-id>/
```

Use an authorized checkout and materialize required Git LFS objects. Read the
asset repository's `AGENTS.md`, `START-HERE.md`, registry, brand metadata,
approved hashes and project approval/state record. Record the repository
revision, exact path, SHA-256 and approval identity in `catalogue.json`.
`incoming/` and unapproved `working/` files are never consumer sources. A
developing brand may have a project-approved exact master while
`current_release` is null; this must be explicit in its project record.

## Commands

```sh
python3 services/kodi/astertv-design/build_pattern_library.py --check
python3 -m unittest discover -s services/kodi/astertv-design/tests -p 'test_*.py'
```

The build is deterministic. `--check` fails if generated files differ from the
committed outputs. Runtime assets are indexed from repository bytes and carry
their SHA-256 hashes. Private release archives are represented by their
published immutable archive hashes; they are not copied into Git.

## Rules

- Limestone-backed compass icons are reserved for the floating side rail.
- Top rails, pills and navigation use the plain compass family.
- Resting artwork has no selection box. Focus uses narrow jade top/sides and a
  deeper title treatment.
- Buttons retain their dimensions and contour in every state. Focus sharpens
  the champagne-gold rim and adds jade without layout movement.
- Current-but-unfocused context is gold, not green.
- Every interactive page has an explicit closed focus graph with entry, Back,
  return-focus and scrolling behavior.
- Synthetic fixtures contain no account, camera, watch-history or credential
  data.

The generated pattern library is review evidence, not owner acceptance. A new
pattern remains `candidate` until the product owner accepts it.
