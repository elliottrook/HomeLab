# D4 candidate-g r5 capture-projection NO-GO — 2026-11-04

## Terminal result

Booking `aster-stream-a-sa3-envelope-20261104-1430-r5` is spent and **NO-GO**.
It claimed exactly at 14:30:00, ended at 14:33:06 after 186 seconds, and
retained `OWNER_TRANSACTION_FAILED_RESTORED` at `owner-transaction` with
`production_restored=true`. No candidate result exists. The retained owner
error remained `candidate-g listener exited nonzero: unclassified guest failure`.

R5 cannot be retried, scored or sent to blind review.

## Independent restoration

Lease returned ready; Doctor was healthy with no codes; no drain/shared lock,
listener, transient guest scope or candidate process remained; LXC104/110/116,
Aster Agent, accepted llama, Speech, News, EPUB, Lab Hours Doctor and Proxmox
services were healthy; core service restart counts remained zero.

## Measured correction path

A harmless content-free target probe confirmed that a guest JSON error written
through `pct exec 110` reaches the host subprocess's stderr. The normal channel
is therefore correct. R5 proves only that its raw capture had no JSON shape the
installed parser could accept; required cleanup prevents reconstructing the
exact deleted bytes.

Mirrored platform commit `7a360b3b2d093f0110736294bfdd9e2899f07d34`
adds a bounded projection sequence across both channels: JSON code, traceback
class only, then process exit status and channel byte counts. It retains no raw
text, prompt, answer, case ID or exception message. The corrected adapter is
`101ce58e…e3c9f`; matching v7 manifest is `1d18a86d…d9537`.

Focused tests pass 30/30 and direct target capture proof passes. The correction
is source-only. A reversible inactive adapter/manifest installer and exact
installed-path proof are next. No fresh booking is eligible before that gate.
