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
listener process group on timeout or failure. A normally exited listener is
not signalled again. The transaction retains the validated result and performs
the existing production restore path.

The source hash is
`4004474a9f78c6abd63b0edef26381de6458d65f4e74a9f4d094ee4ae1a58c51`.
The adapter and transaction boundary tests pass **30/30**.

This card does not install the LXC110 target, create a service, book or check a
Lab Hours window, schedule execution, invoke a model, change the backend,
restart production, or alter the installed `WORKLOAD_RUNNER_UNAVAILABLE`
fail-closed gate.
