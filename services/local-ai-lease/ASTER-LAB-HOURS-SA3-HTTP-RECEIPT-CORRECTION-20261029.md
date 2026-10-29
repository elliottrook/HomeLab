# SA3 HTTP and receipt correction — 2026-10-29

## Observed failure

The booked `aster-stream-a-sa3-20261029-1355` transaction claimed at its
reserved start, drained the fixed consumers, started the accepted Qwen 3.5 9B
SYCL listener, retained 20 bounded rows and restored production. Every row was
invalid with `HTTPError`. The wrapper supplied `/v1` to a transport that expects
the complete chat-completions endpoint, so all twenty calls received an
immediate endpoint error. The reserved runner then rejected the otherwise
restored owner receipt as `OWNER_RECEIPT_INCOMPLETE` because its generic
three-field equality check could never accept the SA3 digest and error-count
fields. Live postcheck proved the accepted services healthy, the lease ready,
all drain and operation locks absent, and the spent guardian was stopped.

## Correction

The installed correction makes four bounded changes:

- the guest wrapper uses exactly
  `http://127.0.0.1:11436/v1/chat/completions`;
- any non-empty SA3 error list now fails the transaction instead of creating a
  success receipt;
- a successful SA3 owner receipt explicitly states
  `production_restored=true` and retains only the result digest, request count
  and zero error count;
- the reservation runner independently completes production postcheck before
  accepting the receipt, validates the exact SA3 receipt shape and digest, and
  can therefore report restoration truthfully on a later receipt failure.

The source tests for the wrapper, transaction, listener adapter and reservation
runner pass. The host manifest pins the corrected transaction and runner.

## Installed result

The live correction used checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-http-receipt-correction-v1`. No SA3
booking was active. It replaced three Proxmox files and one LXC110 wrapper,
then passed the installed manifest/import checks without starting a service,
listener, model request, lease or timer.

Installed SHA-256 values:

- `sa3_expanded_quality_transaction.py` —
  `f2d52b12d99acadfa2f89603449988a16de66017ab10087b550f57703ccbacc0`;
- `lab_hours_reserved_runner.py` —
  `b0579535b8a762686a4299aff8d06d6aad9a2b24d78cc2990edd76e186050b28`;
- `lab_hours_release_manifest.json` —
  `804dbcd6f2b30708970584cc671e9da779aaf1e459a133fe7c8f91d5df9151fd`;
- LXC110 `aster-llama-lab-sa3` —
  `50b13c3f8627c910a1e298470aee7528705a9b4a8905f56c036a2f554dd724cf`.

The next run must use a new authoritative booking after the failed booking's
restoration buffer. It is a fresh attempt, not a retry of the spent booking.
No model, backend, routing, authority or recurring schedule changed.
