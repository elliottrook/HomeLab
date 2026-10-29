# SA3 Lab Hours listener adapter — inactive source card

Status: **source-only; not installed, deployed or wired into reservations**

`sa3_listener_adapter.py` defines the only accepted LXC110 listener command for
`sa3-expanded-source-quality-v1`:

- fixed target `/usr/local/sbin/aster-llama-lab-sa3` in LXC110;
- fixed profile, port `11436`, 20 requests, 120-second request limit and
  2,700-second deadline;
- deterministic lease/generation-bound scope identity; and
- no booking-supplied command, endpoint, model, credential or packet path.

The adapter heartbeats the existing guardian while polling, bounds canonical
result output to 262,144 bytes, validates the transaction's exact packet/model/
case identities, rejects malformed or nonzero results, and terminates the exact
listener process group on timeout or failure. Capture is root-only, file-backed
and bounded so a listener cannot deadlock behind a full stdout/stderr pipe; a
caller also cannot extend the fixed 2,700-second deadline. A normally exited
listener is not signalled again. The transaction retains the validated result
and performs the existing production restore path.

The source hash is
`eb3b304ffc7315c7f8c3deaa06900f2c52a3af256834c701f0fa59c0fe52bc3b`.

The fixed guest wrapper source is
`scripts/local-ai/aster_llama_sa3_guest_wrapper.py`, hash
`27949ff1ba37f825de8d3c4aaeaf6388b9535e72d0063e46eac0e491a6604303`. It pins
the accepted `aster-qwen3.5-9b` model and SYCL server, imports only the four
reviewed runtime files, rejects answer keys and review material, uses an
ephemeral private API key, binds the listener to the lease/generation scope,
and removes the scope and private runtime directory on every exit path. The
adapter, wrapper and transaction boundary tests pass **43/43**.

This card does not install the LXC110 target, create a service, book or check a
Lab Hours window, schedule execution, invoke a model, change the backend,
restart production, or alter the installed `WORKLOAD_RUNNER_UNAVAILABLE`
fail-closed gate.
