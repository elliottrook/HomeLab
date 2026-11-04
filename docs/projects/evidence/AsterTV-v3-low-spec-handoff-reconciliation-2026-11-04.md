# AsterTV v3 low-spec handoff reconciliation

> Status: accepted as measured lab evidence; no deployment authorization.

## Source and live reconciliation

The handing-off agent committed the final qualification as `24926cea` with the
full report at `services/kodi/astertv-v3/low-spec/EVIDENCE-2026-11-04.md`.
The commit contains the Jen-only Jellyfin client policy, the exact-hash Arc
server companion, tests and recovery evidence. It is a descendant of the
pre-handoff contract commit and does not replace Family or Bedroom policy.

A read-only check after handoff confirmed:

- host `AsterTV-Jen` at the reserved address responds using its pinned key;
- Kodi is active after about 2.3 hours uptime;
- `astertv-jen-jellyfin-policy.service` is enabled and its path watcher active;
- current policy is `selective`, HEVC direct play is capped at width 1920 and
  requested bitrate at 18,000 kb/s; patched add-on SHA is `e4715278…d6d89b`;
- the pre-Kodi release guard last returned `Result=success` / status 0 and all
  528 accepted files verify clean; and
- `systemctl --failed` is empty.

Kodi's HTTP JSON-RPC listener is not available on loopback. This is not treated
as a defect or widened for convenience; lab automation must use the established
control path or explicitly design a bounded bridge later.

## Accepted capability interpretation

The machine is accepted as the replaceable v3 low-spec lab for the complete
tested v2 feature set, with these constraints:

- the client acceptance envelope is 1920×1080 at 18 Mb/s;
- Haswell hardware decodes H.264/MPEG-2/VC-1/JPEG, not HEVC/VP9/AV1;
- wider HEVC, including 4K, must transcode through Jellyfin's verified Arc A380
  path to 1080p H.264; direct compressed 4K proved possible but consumed the
  CPU/thermal margin and is not an accepted operating mode;
- HDMI stereo is accepted; passthrough is unsupported on this lab target and
  cannot be used to infer Family's Dolby/HDR result;
- initial Music synchronization is the highest observed memory/start-stop load;
  steady operation passed, but future soak must include first sync and restart;
- plugin URL opens may be synchronous while playback has already begun, so
  automated tests must observe them asynchronously instead of declaring a
  player hang;
- YouTube account authorization remains intentionally absent; and
- Aster AI remains intentionally uncredentialed until M3 creates the dedicated
  capability-scoped identity and broker contract.

The normalized machine-readable profile is
`services/kodi/astertv-v3/contracts/client-capability-jen.json`. Future code may
select that measured profile but must not scatter `AsterTV-Jen` hostname checks
through features. Privacy, focus/navigation, recovery and credential isolation
cannot be reduced for low-spec operation.

## Next safe use

The box can host M2 synthetic accounts and M3 synthetic broker/capture work in
an isolated v3 candidate. Before changing it, record a new bounded authorization
envelope, confirm playback idle, checkpoint the accepted release and profile,
and retain the current v2.0.7/528-file guard rollback. Family and Bedroom remain
out of scope. The first live candidate must test first Music sync, asynchronous
plugin opens, 1080p playback, server-transcoded 4K, restart and guard recovery.
