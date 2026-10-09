# The Contrasting Frame — brand and website style guide

Status: Adopted visual baseline from Jason's accepted website, 2026-10-09.
Owner: Jason Elliott. Scope: every Contrasting Frame surface, public or private.

## Intent

A living photography gallery: refined and professional, but warm, intimate,
unintimidating and quietly whimsical. Photographs and Jason's words are the
subject; the interface is their quiet frame. Avoid corporate polish that feels
cold, luxury theatre, jokey branding, clutter and generic dashboard styling.
The TCF initials are a personal continuity, not an invitation to literal imagery.

## Accepted reference and source

Reference: https://the-closet-fatman-photography.neat-pixie-1264.chatgpt.site/
The legacy hostname is not the current brand name. Destination domain:
`thecontrastingframe.com` (owner-reported ownership; DNS cutover not completed).

Accepted source in this Mac workspace:
`sites/the-closet-fatman/dist/`, commit
`5b23ccb9d8d746196948246f936427495220ed28` in its separate Sites repository.
`styles.css` and supplied SVGs are the executable design baseline. Preserve
the latest accepted source before migration; do not rebuild from memory.
The latest layout has a warm-paper Photographer section and image-led galleries.

## Palette

| Role | Value | Application |
|---|---|---|
| Rich black | `#0b0b0b` | gallery and quiet dark sections |
| Charcoal | `#171717` | restrained supporting surface |
| Warm paper | `#ece8df` | Photographer and Contact; light editor surfaces |
| Antique gold | `#c49a5a` | restrained identity, short labels and dividers |
| Dark bronze | `#8a6635` | gold-like accents on light backgrounds |
| Silver | `#a7a7a7` | secondary dark-surface metadata, subject to contrast tests |
| Warm ink | `#37342e` | handwritten paragraphs on paper |
| Pale story ink | `#d4cabe` | story paragraphs on dark backgrounds |

Do not import Aster navy, cyan/mint glow or its rounded-card visual system.
Gold and silver are not automatically accessible at small sizes: use darker
ink on light surfaces or lighter text on dark ones where contrast requires it.
Text on photos needs a deliberate local scrim; do not obscure the entire image.

## Typography

- Cinzel, regular/light visual weight, for display titles and photograph names.
- Montserrat, generally 300–500, for navigation, metadata and practical UI.
- **dearJoe 4 Regular PRO** for story paragraphs and the Photographer quote.
  The Contrasting Hand and comparison variants are retired, not fallbacks.
- Stories: desktop baseline 28–30 px with 1.6–1.8 line height; mobile 26–28 px
  where comfortable. Keep paragraphs short, tracking neutral, and measure
  roughly 35–45 rem or less. Test the actual font rather than matching numbers.
- Handwriting is for authored narrative, not controls, errors, tables or long
  operator instructions. Editor source text may use a readable sans-serif;
  its preview renders the handwritten narrative.
- Preserve ligatures and normal flow. Avoid fake-bold, outlined/thickened
  lettering, decorative font effects or excessive letter spacing in stories.
- Fonts must be served under their actual licences. Keep commercial font files,
  purchase proof and EULAs private; verify the licensed production domain,
  preview environments and traffic allowance before launch. Never include them
  in a public GitHub mirror or source download. Prefer locally served authorised
  fonts over third-party browser calls; do not substitute without Jason's review.

## Logos and assets

Use the supplied full-colour camera, horizontal mark, monogram and signature.
Respect proportions, clear space and fine strokes. No new interpretation of
the camera, heavy effects, stretching, rotation or routine AI regeneration.
Use the dark-lettering full-colour camera variant on warm paper:
`camera-logo-colour-light.svg`. Use the website dark-background variants where
appropriate. Light lettering must never disappear into a light surface.
The signature is a quiet sign-off, not repeated decoration around every photo.

## Page composition

- Home: expansive opening photograph; a short story; The Photographer on warm
  paper with full-colour camera; Field Notes; warm-paper Contact.
- Collections: Landscapes, Flora, Contrasts (black and white), People.
- Each collection opens with one image-led viewport rather than an empty title
  page. For a landscape opening, embed the story over the picture with readable
  contrast and unobstructed visual interest. For a portrait opening, place the
  photograph and story alongside each other.
- Remaining work uses one photograph and one story per row. Alternate image
  left/story right, then story left/image right. No two-photo grids or rows of
  photographs detached from their words. Stack responsively on small screens,
  always keeping the corresponding story with its photograph.
- A full-image viewer may reveal the uncropped image and associated story.
  Thumbnail/hero cropping is explicit; never alter a master photograph.
- Generous breathing room is intentional, but do not recreate the rejected
  empty gallery header. Navigation remains discreet, useful and keyboard usable.
- Thin dividers, restrained links, square photographic edges and little chrome.
  No card carousel, animated spectacle or commerce-led homepage in this phase.

## Editorial voice and truth

Warm, observant, patient and lightly humorous. A small human moment is better
than grand claims about the sublime. Jason's writing owns the voice; AI is a
collaborator, never an unreviewed replacement. Preserve originals and show diffs.
Clearly distinguish fictional vignettes from factual accounts, especially for
people. Never invent a subject's identity, consent, quotation, location or life.
Alt text describes what is visible, not the fictional story. Private notes,
precise GPS and client details must not leak into public output.

Stock/demo images require attribution/provenance and must not be represented
as Jason's photographs or offered for sale as his work. Existing fiction and
stock are placeholders, not launch-ready content by default.

## Editorial tool and accessibility

A private Content Desk belongs to this brand: warm paper, fine dividers, quiet
gold accents and readable sans-serif editing controls. Show photograph, story,
AI suggestions/diff, rights, approval and scheduled date together. Use plain
statuses: Draft, Needs review, Approved, Scheduled, Published, Failed.
No public route to the editor. Security does not change the brand styling.

Support keyboard navigation, visible focus, labelled image controls, modal
Escape/close/focus return, useful alt text and reduced motion. Aim for WCAG AA
text contrast and comfortable touch targets. Check desktop and 390 px mobile
with both portrait and landscape content and long handwritten paragraphs.

## Acceptance and change control

Preserve the accepted look through migration. Review a real image/story pair
and a private editor preview with Jason in the initial design milestone.
Substantial typography, colour, logo or layout changes require his explicit
design acceptance. Record screenshot evidence and an operator walkthrough at
graduation. Update this guide when a new design is actually accepted, not when
an agent merely proposes one.
