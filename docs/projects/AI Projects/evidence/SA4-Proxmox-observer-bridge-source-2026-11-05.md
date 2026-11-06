# SA4 Proxmox observer bridge source — 2026-11-05

The matching Proxmox half of the fixed observer exchange is now source-complete.
For sequence one or two it performs only a fixed `pct pull` from LXC 104,
validates the complete canonical statement, invokes only the bounded installed
observer signer, writes one root-only signature response, and performs only a
fixed `pct push` back to LXC 104.

The bridge accepts no command, path, VMID, key or payload parameter. Duplicate
local state fails closed. Pull failure occurs before signing; push failure
retains the validated request and signature for reconciliation. It never reads
or exports the observer private key itself.

Four focused tests cover the exact command sequence, custody/duplicate drift,
pull failure and response-delivery failure. The complete SA4 suite passes
180/180. The source is not installed. Next is a joined disposable rehearsal of
the LXC exchange, Proxmox bridge and one-shot controller, followed by an exact
inactive-install packet and review.
