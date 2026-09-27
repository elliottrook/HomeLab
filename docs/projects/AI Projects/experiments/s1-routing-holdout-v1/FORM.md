# S1 blank local collection form

Status: **blank pre-collection artifact; do not enter a case before approval**.

Complete one JSON case object and one acceptance object per family in the local
bundle. The helper validates syntax and hashes only. It does not suggest labels,
authenticate the human, prove privacy, authorize collection or stage files.

| Field | Human-supplied value |
|---|---|
| Case/family ID and revision | |
| Stratum | |
| Sanitized request using placeholders | |
| Accepted status set | |
| Required capabilities | |
| Optional capabilities | |
| Prohibited capabilities | |
| Sensitivity | |
| Cloud class | |
| Failure behavior | |
| Constraint tags | |
| One-sentence observable reason | |
| No secrets | unchecked |
| No identifiers | unchecked |
| No exact private context | unchecked |
| No copied conversation | unchecked |
| Placeholders only | unchecked |
| Content decision for exact hash | |
| Label decision for exact hash | |
| Durable sanitized local-Git retention accepted | unchecked |
| Accepted-at timestamp | |

Rules:

- Jason writes the request and labels without engine output or AI suggestions.
- Use placeholders such as `[PERSON]`, `[EVENT]`, `[PLACE]`, `[SITE]` and
  `[SYSTEM]`. Public facts that define the task class may remain public.
- Never enter credentials, tokens, internal addresses, account identifiers, exact
  private event text or copied conversation logs.
- Every prohibited list includes all four `always_prohibited` registry entries.
- Hash the exact case object using canonical compact sorted-key JSON. The validator
  reports a mismatch without printing the request.
- Keep drafts only in the approved scratch location. Only accepted sanitized
  records may enter Git, and no push is implied.

See `bundle-template.json` for the machine-readable empty envelope and
`registry.json` for the complete permitted vocabulary.
