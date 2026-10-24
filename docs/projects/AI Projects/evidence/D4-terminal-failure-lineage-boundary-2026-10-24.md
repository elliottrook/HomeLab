# D4 terminal/failure lineage boundary — 2026-10-24

## Finding

The private SA3/D4 journal validator already required `conclude` and `clarify`
statuses to match the final retained answer. The inverse was not enforced: a
nonterminal failure status could still retain a terminal answer. A terminal
status could also carry transport-failure metadata, and a transport failure's
attempt count was not bound to the retained successful steps plus the failed
attempt. One row could therefore describe incompatible terminal and failure
states even though no live action was possible.

The investigation engine also retained a rejected answer before assigning
`effect_claim_rejected`, `unobserved_evidence_rejected` or
`invalid_terminal_check`. The private journal is owner-only, but retaining an
answer already rejected by policy was unnecessary.

## Correction

- The producer discards the rejected answer for effect claims, unseen evidence
  and a terminal decision carrying a check.
- A nonterminal engine status cannot retain a `conclude` or `clarify` answer.
- Transport-error status and non-null failure metadata must appear together.
- A transport error's attempted-call count must equal retained steps plus the
  one failed call; every nontransport count must equal retained steps.
- Resume revalidates these rules for each existing finished journal event.

The complete evaluation suite passes 128/128 under Python 3.12.14. The run used
only synthetic fixtures and injected transports. No holdout was opened, model
called, tool connected, route enabled or production service changed.

This correction protects evidence consistency. It does not establish answer
quality, complete D4, grant AI-PAM authority or release a sysadmin role.

