# AsterTV v3 pre-handoff contracts

These files are synthetic repository contracts created under the bounded
pre-handoff Stream A. They contain no live account, credential, history, camera
or library data and perform no network or client action.

- `v2-workflows.json` freezes the user-visible navigation/playback behaviours
  that v3 must preserve.
- `account-profile-contract.json` proposes the minimum profile registry and
  guest-denial boundary without embedding service credentials.
- `client-capability-profile.schema.json` lets the low-spec handoff describe
  measured limits without scattering hostname checks through features.
- `client-capability-jen.json` is the reconciled measured 1080p/Haswell lab
  profile; it requires server transcode for wider HEVC and declares no audio
  passthrough.
- `aster-broker-contract.json` is the adopted Jen-pilot AsterTV intent surface:
  independent authentication, recovery-admin profile boundary, deterministic
  allowlisted grammar and explicit denials for M3.

The low-spec report is reconciled. The account contract is implemented by the
bounded Jen-only M2 authority under `../accounts/`; its dedicated Guest mapping
and the independently resolved `aster_tv` identity are the only exceptions to
the original credential-free synthetic registry. The M3 broker and Jen client
under `../aster_client/` are active only for the Jen pilot. G20 capture and Home
aliases remain explicit deferred gates; other household profiles and targets
remain undecided. `test_contracts.py` is a structural fail-closed gate and the
client tests prove the behavioural adapters and live denial boundary rather
than weakening these invariants.
