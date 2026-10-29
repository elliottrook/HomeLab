# SA3 expanded-source runtime correction — 2026-10-29

The second booked evaluation claimed on time and completed its fixed drain and
restoration transaction, but it did not produce usable quality evidence. All
20 retained rows were invalid with `HTTPError`; the terminal state correctly
remained `NO-GO`. Production services, the accepted 9B/SYCL stack and Proxmox
daemons were healthy afterward, the whole-host lease returned ready, no drain
or operation lock remained, and the spent guardian was stopped after that
independent postcheck.

The error was deterministic: the guest wrapper passed `/v1` to a transport
that requires `/v1/chat/completions`. A separate receipt validator also used a
generic exact comparison that could never accept the SA3 digest/error metadata
and recorded restoration as false even after the live stack had restored.

The platform correction now:

1. calls the exact loopback chat-completions endpoint;
2. rejects any non-empty transport/runtime error list;
3. includes an explicit successful restoration assertion in the bounded owner
   receipt; and
4. performs production postcheck before receipt acceptance and validates the
   exact SA3-specific receipt.

The focused source suites pass and the four corrected live files match their
reviewed hashes. Installation retained a rollback checkpoint and caused no
service stop, listener, lease, model request, restart or scheduling effect.
A distinct booking may run only after the failed booking's restoration buffer
and a fresh authoritative ledger check.
