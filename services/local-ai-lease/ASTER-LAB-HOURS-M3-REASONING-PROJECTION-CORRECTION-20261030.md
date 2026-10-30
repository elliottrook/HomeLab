# M3 reasoning projection correction — 2026-10-30

Status: **SOURCE CORRECTED; SPENT 12:16 BOOKING NOT RETRIED**

Booking `aster-stream-a-m3-35b-20261030-1216` reached all 24 public requests.
Every engine response completed transport but failed the strict response parser:
`attempted=24`, `valid=0`, `first_record_failure=invalid_response`. Production
restoration passed and the lease returned to ready.

The 35B service intentionally ran with reasoning enabled. Its OpenAI-compatible
message can therefore contain the additional `reasoning_content` field. The
shared parser passed the complete message to the final-answer parser, whose
privacy boundary correctly accepts only `role` and `content`; all 24 otherwise
completed responses were consequently rejected.

The correction validates that the message is exactly `role`, `content` and an
optional string-or-null `reasoning_content`, then constructs a new transient
envelope containing only `role` and `content`. The hidden reasoning is neither
parsed nor retained. Any other message field or type still fails closed. A
regression proves 24/24 projected responses are valid and that the private
reasoning marker is absent from retained results.

The same change fixes the bounded terminal projection's field collision:
transaction `failure_code` can no longer be overwritten by the guest's nested
failure code. A later restored failure can therefore become a specific terminal
code instead of falling back to `OWNER_TRANSACTION_FAILED_RESTORED`.

The focused diagnostic, guest, transaction and booked-runner suite passes
19/19. All release pins are updated. This source change schedules no run,
starts no model, reads no credential, opens no holdout and enables no routing.
