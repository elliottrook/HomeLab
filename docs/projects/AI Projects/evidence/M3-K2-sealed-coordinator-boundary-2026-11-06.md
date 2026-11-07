# M3 K2 sealed coordinator boundary — 2026-11-06

## Outcome

The Mac mini coordinator for one future K2 sealed-evaluation transaction is
source-frozen. Both required SSH tunnel directions were independently proven
with temporary harmless loopback endpoints and fully torn down. The coordinator
itself was tested only with synthetic fixtures; no B60 or sealed-evaluation
effect occurred.

## Exact source

- coordinator: `scripts/aster-adaptive/nlu_k2_sealed_coordinator_v1.py`
- coordinator SHA-256: `e5fa5e6a37c94516bafb3660d67bf0dadc26ac7f006a6fdceab4802dd4241861`
- focused test SHA-256: `4b258c148725c725e42ff855ce62cbbf98c0095f6f25cb71b31b4a14eb54df96`
- preregistration digest: `4e7754585aeeef597c66eb2d3f2c6bf673f140f35c2f06d1856274429580adb1`

The coordinator accepts only a current content-free ready-session descriptor
and two root-custodied mode-0600 nonce files whose byte digests match that
descriptor. It starts one loopback-only upstream SSH forward, one loopback
relay, one loopback-only reverse SSH forward to the MacBook, and one fixed
MacBook wrapper. The relay nonce is passed to the wrapper only on standard
input. No secret is embedded in a command line or returned in evidence.

Exactly 32 no-retry requests and a matching wrapper/relay terminal are required
for success. Every child is terminated in reverse order and both local nonce
files are removed on every terminal path. The coordinator never receives the
sealed evaluation, request text, expected labels, records or private metrics.

## Live tunnel proof

Two independent, non-B60 probes used alternate ports and no private content:

1. Mac mini `127.0.0.1:15438` was exposed only as MacBook loopback
   `127.0.0.1:15437` through the established `ssh -R` path. A MacBook curl
   received HTTP 200. The SSH tunnel and temporary HTTP server were stopped,
   and both ports then refused connections.
2. Mac mini `127.0.0.1:15439` was forwarded through the existing authenticated
   Proxmox SSH path to Proxmox loopback TCP/22. A TCP probe succeeded; the
   tunnel was stopped and the local port then refused connections.

This proves the coordinator's two loopback tunnel directions. It does not
prove or authorize the future private model listener on port 11436.

A fresh read-only recheck before the booked K2 development transaction also
confirmed that the Mac mini's existing `macbook` SSH alias authenticates in
BatchMode to `Jasons-Mac.local` as the expected non-root user. No tunnel,
listener or remote file was created by that recheck. The required control
direction is therefore currently available without a new access grant.

## Verification

- coordinator/wrapper/relay suite: 11/11 passed
- combined coordinator/preregistration/wrapper/relay suite after the final
  twelve-pin refresh: 16/16 passed
- Python syntax compilation: passed
- external temporary processes: stopped; probe ports closed
- model requests and B60 use: zero
- platform session contract refreshed to the final preregistration at commit
  `1a0f48da`, 5/5 focused tests

## Remaining gate

The platform private-listener/session implementation, release-manifest entry,
inactive installation and distinct Lab Hours reservation remain absent. They
must not proceed unless the current K2 development transaction completes with
a passing gate and production restored.
