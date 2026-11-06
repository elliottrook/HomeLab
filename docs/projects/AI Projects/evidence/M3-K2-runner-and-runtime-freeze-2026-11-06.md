# M3 K2 transaction runner and runtime freeze — 2026-11-06

**State: complete source candidate; not installed or invoked.**

The K2 one-attempt runner now binds the exact accepted corpus and content-free
shortlist artifact, the accepted production 9B/SYCL identity and every source
dependency. It permits exactly 192 requests, zero retries, a 45-second per-case
timeout and a 1,800-second wall deadline. Before each request it durably writes
an owner-only journal event. Any transport, response, parser or evidence error
stops the run before another request.

The response projection accepts only bounded llama/OpenAI metadata, rejects
reasoning or tool calls, and passes only role/content plus clean completion to
the strict K2 parser. The create-only result and journal are mode `0600`; they
retain no request text, raw response text or credential. The runner itself
does not acquire a booking, lease or operation lock; the registered platform
transaction must provide and verify those external controls.

The runtime manifest pins the live read-only observed production identities:

- `aster-llama.service` unit:
  `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`
- accepted SYCL server:
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`
- accepted 9B model:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`
- observed service: active/running, `NRestarts=0`
- observed whole-host lease: exactly `ready`

Frozen source evidence:

- runner SHA-256:
  `ea0f2fb2156439364e723ae0b3076f9112d21da6136379521ee1f95946041d63`
- runner test SHA-256:
  `2609aee2ee65487a45e99016d221fc59b9ba4a9dfcd63b02a46ec2e4b6f77e77`
- runtime manifest SHA-256:
  `247b29213f11ddd86a9cfa8bb1c72894473ef9fde3c9428b66be8fe580b73d79`
- runtime validator SHA-256:
  `c397d4a367ac083f22cc17f5611d9371daa89c5dd59dd261a1c4494e3e49acd8`
- runtime test SHA-256:
  `508371f992164817e83c4f3807a569672b2f0070c63b2480561c2d63ccf6cb9a`
- complete K2 focused suite: `30/30` passed
- syntax compilation: passed with an isolated bytecode cache

The minimum later reservation is 3,600 seconds, including a 900-second
recovery reserve. The exact registered workload must be
`m3-k2-shortlist-arbitration-development-v1`. No schedule may be proposed or
created until the authoritative Lab Hours ledger confirms the complete chosen
window. No model call, install, booking, lease, service action, route, tool or
promotion occurred in this source milestone.
