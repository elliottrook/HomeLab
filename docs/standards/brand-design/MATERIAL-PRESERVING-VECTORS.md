# Material-preserving vector reconstruction

Adopted: 2026-10-14 after owner approval of the Aster v2 single-compass proof.
This is a reusable workflow, not a requirement to copy Aster's visual identity.

## The successful path

1. Lock the exact approved colour raster and SHA-256. Inspect native dimensions,
   transparency, silhouette, counters, bevels and texture. Preserve it unchanged.
2. Separate meaningful components: substrate, bearing/rings, individual point
   faces, metal edges, centre motif and lettering. Measure from the colour source.
3. Choose construction by visual evidence. Use smooth paths/gradients for clean
   forms; use source-derived colour contours where mineral grain, engraving and
   irregular metallic light are essential to the approved character.
4. For textured tracing, quantize **per component**, not across the whole image.
   Cluster colour samples with frequency weighting; preserve the light/dark and
   hue split of each face. The approved Aster pilot used 56 colour clusters per
   component, not a universal target for every brand.
5. Trace cumulative masks in luminance order and overlap adjacent contours
   slightly to avoid antialiasing pinholes. Clip to the component's silhouette.
   Retain counters and transparency. Named groups must describe actual parts.
   Build region ownership from binary masks, not anti-aliased numeric label
   colours (blended label values can falsely select unrelated components).
   Match boundaries to real materials; broad geometric masks must not leave
   ghost outlines across adjacent stone or bearing surfaces. Material-gated
   source underlays can fill mismatches but may greatly increase path count.
6. Render the real SVG. Compare raster/vector side by side, native-size and
   enlarged crops, and intended small sizes. Inspect texture, silhouette, light,
   material colour, overlap and exact literal lettering—not just XML validity.
7. Perfect this one asset and record the owner's acceptance of its exact SVG
   hash before rolling out the method. Reject flat or materially different
   results even if geometry is mathematically tidy.
8. Expand the family from verified sources/components. Use identical reusable
   geometry for repeated concepts, preserve requested motif scale/rotation,
   and review all derivatives. Keep an asset-specific coverage matrix.
9. Export PNG/WebP from the verified SVG, audit safety/local references, record
   hashes, reopen the archive and render an extracted copy. Keep working,
   approved-library and deployed-application states distinct.

## Proven implementation and honest trade-offs

The Aster pilot source was **1254 × 1254 native pixels**, not a 3K generated
image. The accepted SVG had **23 named components**, **1245 paths** and
**12 ellipses**, occupying **20,716,840 bytes**. It contained no embedded image,
live text, external dependency or raster filter. Its 3000px PNG was rendered
from vector geometry; that does not create additional native source detail.

Source hash: `279f513a94a1355eb8c8523452e20164b697f2e48f367a2f8b7ac9836c6a5eaf`.
Approved SVG hash: `f6a0f19ff9e5ac4728e04cf20c28e86f171d516ec403a1bc3df937c8a456c6a4`.
Approval: owner said “perfect, thank you” and requested the remaining assets.
Exact source, code, renders and QA are retained in Aster Home's Brand Asset
Library working engagement, `core-component-proof-2026-10-14/`.

This is a high-detail vector illustration, not a lightweight UI icon. Complex
contours remain editable but are harder to manipulate than hand-built gradient
faces. Fine raster grain may soften or become stepped contours; hidden surfaces
are not reconstructed automatically. Changing component positions can require
repair. Disclose these limits before acceptance. Use right-sized PNG/WebP for
runtime delivery when appropriate; retain SVG as the archival/editable master.

The earlier Contrasting Frame work used 1254px, 1536px and 1983px-long source
images with component separation, shading and local vector export. Neither
workflow required separately billed image API credits. Verify currently
available tools rather than promising native 3K generation or imposing an API.

## Failure modes to prevent

- Enlarging a raster and calling it a new high-detail master.
- Treating a flat tracing guide as the appearance authority.
- Replacing distinct gold/jade split faces with one uniform colour.
- Embedding a PNG in SVG and describing it as reconstructed vector artwork.
- Claiming dense automatic contours are a clean, lightweight hand-built logo.
- Reusing another brand's order sheet, colours or typography without checking.
- Scaling the whole family before the first actual SVG render is accepted.
- Shipping matching labels with non-matching reel/archive or other repeated
  symbols; verify reusable component identity, not just approximate resemblance.
- Claiming a browser test when local file access was prohibited; use available
  permitted renderers and disclose unperformed cross-renderer checks.

## Required evidence

Maintain source hashes/dimensions/effective detail, named component map, colour
and tracing parameters, build recipe/dependency versions, vector safety audit,
whole/detail/size comparisons, exact approval evidence, export checksums,
package verification, delivery status and rollback. A family render remains a
candidate until its own visual review; pilot approval is the method gate.
