# AsterTV v3 M10 — knowledge publication

Date: 2026-11-05 local / 2026-11-06 UTC

Status: live knowledge surfaces validated; final evidence synchronization pending

## Repository promotion

The approved Forgejo pushes advanced:

- HomeLab `codex/astertv-v3` to `36b0e01f91721a557c76aebcc0a4eca72c63e5ce`;
- HomeLab Wiki `main` to `fc33f735c8e1338e1409d2f81933192ff9578351`; and
- HomeLab Reference `main` to `62bb587aa692b84d6c672c717e43daa1d0b4a432`.

All three Forgejo refs were read back directly. The configured HomeLab GitHub
protection mirror reached the same Stream A commit. The wiki and reference
repositories have no separate local GitHub remote configured.

## LXC 113 human wiki

Before publication, collector verification passed for 31 live sources. The
existing source manifest, accepted lock, home page and MkDocs configuration
were checkpointed under
`/var/lib/aster-wiki/state/checkpoints/m10-astertv-wiki-fc33f73-20261105/`.

Only the authored AsterTV tree and its navigation dependencies were published;
the live source manifest and generated upstream corpus were not replaced. A
macOS archive initially carried AppleDouble companions. They were detected by
the page-count gate and removed only from the newly created AsterTV directory.
The final live tree has zero AppleDouble objects, exactly 25 Markdown pages and
tree SHA-256 `c38ded62c6d27335b69b4082f3d8974409af3c7da0e6e18fca959a5fca4566ae`,
identical to the validated source tree.

The live home page had a newer Aster Companion route than the local candidate.
It was preserved in corrective local wiki commit
`68711007013d454ef679cce3302b50dd15c8536a`, alongside the AsterTV navigation.
The two already-authored support pages linked by the AsterTV curricula were
published as dependencies. Home, AsterTV, Aster operations and EPUB narration
all return HTTP 200. Corpus-health link drift is zero.

## Reviewed reference and derived mirror

The exact reviewed `operations/astertv.md` bytes were enrolled through the
existing manual intake as `astertv-operational-reference`, without giving LXC
113 a Forgejo credential. The accepted normalized SHA-256 is
`5f8c3a3b13acaea93dead378ca114defac0ea74e3abdd55d61f7926a49d7da9d`,
which matches reference commit `62bb587a…a432`.

The collector completed with zero failures and zero quarantine: 30 sources
were processed and two were unchanged. Verification passes for all 32 accepted
sources. The root-owned mirror parent rejected an unprivileged staging attempt
before mutation; the established atomic double-build was then run with the
required filesystem owner and collector ownership restored.

Final mirror generation:

- pipeline `1.5.0`, prompt `extractive-claims-v1`;
- 1,823 verified entries;
- content SHA-256
  `8c9d44466995617a3c3e83ea335060c23486809547c71a99ec9d736d1d662ee5`;
- 12 AsterTV reference entries and 12 matching provenance links; and
- registered directory abstract for `astertv-operational-reference`.

Corpus health has zero failures, broken links, directory drift, duplicate
claims or unclassified sources. The remaining warning is two pre-existing
Synology installation guides last retrieved on 2026-09-14; it is not caused by
this publication and was not silently re-pinned.

The local integrated gate at source commit
`1fede63bb88a06c2bd5a686d931d92d3464074cf` passed twice with byte-identical
JSON SHA-256
`83f2e868e354489a92b376df05458df43aabad3960a5bf55080c0044f0d824d8`:
54 test files pass, 93 candidate inputs scan clean, all 15 pages and 127 focus
controls conform, and the fail-closed operations audit now reports only the
five explicit Family/restore gaps.

## Recovery

The human-wiki checkpoints retain the previous home/MkDocs files and source
hashes. The reference-intake checkpoint retains the previous manifest,
accepted lock and mirror generation. Collector rollback retains the prior
accepted corpus; mirror build atomically retained the previous tree as
`aster-knowledge-mirror.last-good`. No AsterTV appliance, playback service,
network rule or credential changed.
