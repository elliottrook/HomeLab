# M3 J2 evaluation revision-4 NO-GO and revision-5 correction

## Revision-4 result

Revision 4 is terminal `NO-GO`. Its archive and source checks passed and its
local key generation completed, but the one evaluation command exited `1` with
`ValueError: J2 evaluation case identity or label changed`. No export was
transferred; the Mac mini return directory is empty. The reported local public-
key file SHA-256 `2ad6d8c1…2b33873e` is not accepted and must not be reused.

The failure occurred before evaluation-content, overlap or signature evidence
could be accepted. Private case text remained on the MacBook and was not read
by Stream A.

## Correction

Revision 5 removes agent-selected identities. It fixes all 32 valid case IDs,
enumerates the exact sixteen allowed label IDs with two cases each, and adds a
pure `evaluation-check` command. That command runs the frozen validator and
returns only hashes, counts, seal state and zero-intersection status; it creates
no key or output. A failed preflight is terminal. Key generation and the one
signing command are allowed only after a passing preflight and without changing
the evaluation bytes.

The expanded focused tests pass 8/8. The revision-5 evaluation archive has
SHA-256 `6219da6fe2a922c79244403abc53f13434e776f1f7bd670ae9de6698c35fe8db`;
all thirteen manifest hashes and its isolated import pass. The accepted corpus
custody result remains unchanged and must not be repeated.

The next external action is one fresh session using the
[identity-fixed revision-5 evaluation prompt](M3-J2-EVALUATION-CUSTODIAN-REMOTE-R5-PROMPT-2026-11-06.md).
