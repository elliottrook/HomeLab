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
- `aster-broker-contract.json` proposes the narrow AsterTV intent surface and
  explicit denials for M3.

All are candidates until the M0 decisions are accepted and the low-spec report
is reconciled. They are not deployment inputs. `test_contracts.py` is a
structural fail-closed gate; later milestones must add behavioural adapters and
live denial tests rather than weakening these invariants.
